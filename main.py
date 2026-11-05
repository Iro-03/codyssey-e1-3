import time
import json
import math
from pathlib import Path

def generate_patterns(size):
    """짝수 크기는 아래/오른쪽 중앙선을 십자가의 중심으로 사용한다."""
    if type(size) is not int or size <= 0:
        raise ValueError("크기는 양의 정수여야 합니다.")

    cross = []
    x = []
    center = size // 2
    for row in range(size):
        cross_row = []
        x_row = []
        for col in range(size):
            cross_row.append(1 if row == center or col == center else 0)
            x_row.append(1 if row == col or row + col == size - 1 else 0)
        cross.append(cross_row)
        x.append(x_row)
    return {"Cross": cross, "X": x}


def flatten_matrix(matrix):
    """행 우선 순서로 2차원 리스트를 길이 N²의 리스트로 변환한다."""
    flattened = []
    for row in matrix:
        for value in row:
            flattened.append(value)
    return flattened


def mac_flat(pattern, filter_values):
    if len(pattern) != len(filter_values):
        raise ValueError("1차원 패턴과 필터의 길이가 일치해야 합니다.")
    score = 0.0
    for index in range(len(pattern)):
        score += pattern[index] * filter_values[index]
    if not math.isfinite(score):
        raise ValueError("MAC 점수가 유한한 범위를 벗어났습니다.")
    return score


def compare_mac_layouts(pattern, filter_matrix, repeats=1000):
    if type(repeats) is not int or repeats < 10:
        raise ValueError("성능 비교는 최소 10회 반복해야 합니다.")

    conversion_start = time.perf_counter()
    flat_pattern = flatten_matrix(pattern)
    flat_filter = flatten_matrix(filter_matrix)
    conversion_ms = (time.perf_counter() - conversion_start) * 1000

    # 점수 검증과 준비 호출은 측정 구간에서 제외한다.
    score_2d = mac(pattern, filter_matrix)
    score_1d = mac_flat(flat_pattern, flat_filter)
    if score_2d != score_1d:
        raise ValueError("2차원/1차원 MAC 점수가 일치하지 않습니다.")

    calls = (
        (mac, pattern, filter_matrix),
        (mac_flat, flat_pattern, flat_filter),
    )
    elapsed = [0.0, 0.0]
    for repeat in range(repeats):
        # 먼저 측정하는 구현을 번갈아 바꾼다.
        order = (0, 1) if repeat % 2 == 0 else (1, 0)
        for index in order:
            function, values, weights = calls[index]
            start = time.perf_counter()
            function(values, weights)
            elapsed[index] += time.perf_counter() - start

    return {
        "original_ms": elapsed[0] / repeats * 1000,
        "flat_ms": elapsed[1] / repeats * 1000,
        "conversion_ms": conversion_ms,
        "repeats": repeats,
    }


def print_optimization_comparison(performance_cases):
    print("\n1차원 배열 최적화 비교: 동일 입력, 각 1000회 평균")
    print("크기 | 2차원(ms) | 1차원(ms) | 2차원/1차원 배율 | 변환 1회(ms)")
    for size in sorted(performance_cases):
        pattern, filter_matrix = performance_cases[size]
        result = compare_mac_layouts(pattern, filter_matrix)
        original_ms = result["original_ms"]
        flat_ms = result["flat_ms"]
        ratio = f"{original_ms / flat_ms:.2f}x" if flat_ms > 0 else "측정 불가"
        print(
            f"{size}×{size} | {original_ms:.6f} | {flat_ms:.6f} | "
            f"{ratio} | {result['conversion_ms']:.6f}"
        )
    print("배율이 1보다 크면 1차원이 빠릅니다. 변환 시간은 MAC 평균에서 제외합니다.")


def mac(pattern, filter_matrix):
    score = 0.0
    size = len(pattern)

    for row in range(size):
        for col in range(size):
            score += pattern[row][col] * filter_matrix[row][col]

    if not math.isfinite(score):
        raise ValueError("MAC 점수가 유한한 범위를 벗어났습니다.")

    return score

def judge(score_a, score_b, label_a, label_b):
    epsilon = 1e-9

    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"

    if score_a > score_b:
        return label_a

    return label_b

def normalize_label(label):
    if not isinstance(label, str):
        raise ValueError("라벨은 문자열이어야 합니다.")

    label = label.strip().lower()

    if label in ("+", "cross"):
        return "Cross"

    if label == "x":
        return "X"

    raise ValueError(f"알 수 없는 라벨: {label!r}")

def parse_case_size(case_id):
    parts = case_id.split("_")

    if (
        len(parts) != 3
        or parts[0] != "size"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise ValueError(f"잘못된 케이스 키: {case_id}")

    size = int(parts[1])
    index = int(parts[2])

    if size <= 0 or index <= 0:
        raise ValueError(f"크기와 번호는 양수여야 합니다: {case_id}")

    return size

def validate_matrix(matrix, size, name):
    if not isinstance(matrix, list) or len(matrix) != size:
        raise ValueError(f"{name}: 행 수가 {size}개여야 합니다.")

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(
                f"{name}: {row_index + 1}행의 열 수가 "
                f"{size}개여야 합니다."
            )

        for value in row:
            if type(value) not in (int, float):
                raise ValueError(
                    f"{name}: {row_index + 1}행에 숫자가 아닌 값이 있습니다."
                )

            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False

            if not finite:
                raise ValueError(f"{name}: 유한한 범위의 숫자를 입력해야 합니다.")

def read_matrix(name, size):
    print(f"\n{name}: 각 행에 숫자 {size}개를 공백으로 구분해 입력하세요.")
    matrix = []

    for row in range(size):
        while True:
            text = input(f"{row + 1}행: ")

            try:
                values = [float(value) for value in text.split()]
            except ValueError:
                print("입력 형식 오류: 숫자만 입력하세요.")
                continue

            if len(values) != size:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요.")
                continue

            if not all(math.isfinite(value) for value in values):
                print("입력 형식 오류: NaN이나 무한대 대신 유한한 숫자를 입력하세요.")
                continue

            matrix.append(values)
            break

    return matrix

def measure_mac(pattern, filter_matrix, repeats=10):
    if repeats < 10:
        raise ValueError("성능 측정은 최소 10회 반복해야 합니다.")

    total_seconds = 0.0

    for _ in range(repeats):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()

        total_seconds += end - start

    return total_seconds / repeats * 1000

def print_performance(pattern, filter_matrix):
    size = len(pattern)
    average_ms = measure_mac(pattern, filter_matrix)

    print("\n성능 분석: MAC 함수 10회 반복 평균")
    print("크기       | 평균 시간(ms) | 연산 횟수(N²)")
    print(
        f"{size}×{size:<7} | "
        f"{average_ms:.6f}      | "
        f"{size * size}")

    print_optimization_comparison({size: (pattern, filter_matrix)})


def print_json_performance(performance_cases):
    print("\n성능 분석: MAC 함수 10회 반복 평균")
    print("크기 | 평균 시간(ms) | 연산 횟수(N²)")

    for size in (3, 5, 13, 25):
        if size not in performance_cases:
            print(f"{size}×{size} | 측정 불가: 유효한 데이터 없음")
            continue

        pattern, filter_matrix = performance_cases[size]
        average_ms = measure_mac(pattern, filter_matrix)

        print(f"{size}×{size} | {average_ms:.6f} | {size * size}")

def run_manual_mode():
    filter_a = read_matrix("필터 A", 3)
    filter_b = read_matrix("필터 B", 3)

    print("\n필터 저장 확인")
    print("필터 A:", filter_a)
    print("필터 B:", filter_b)

    pattern = read_matrix("입력 패턴", 3)

    try:
        score_a = mac(pattern, filter_a)
        score_b = mac(pattern, filter_b)
    except (ValueError, OverflowError) as error:
        print(f"연산 오류: {error}")
        return
    result = judge(score_a, score_b, "A", "B")

    print("\nA 점수:", score_a)
    print("B 점수:", score_b)
    print("판정:", result)
    print_performance(pattern, filter_a)

def run_generated_mode():
    while True:
        try:
            size = int(input("생성할 패턴의 크기 N (양의 정수): "))
            patterns = generate_patterns(size)
            break
        except ValueError as error:
            print(f"입력 오류: {error}")

    for label, matrix in patterns.items():
        print(f"\n생성된 {label} 패턴 ({size}×{size})")
        for row in matrix:
            print(" ".join(str(value) for value in row))

    while True:
        try:
            label = normalize_label(input("입력 패턴 선택 (Cross/+ 또는 X): "))
            break
        except ValueError as error:
            print(f"입력 오류: {error}")

    pattern = patterns[label]
    score_cross = mac(pattern, patterns["Cross"])
    score_x = mac(pattern, patterns["X"])
    print("\nCross 점수:", score_cross)
    print("X 점수:", score_x)
    print("판정:", judge(score_cross, score_x, "Cross", "X"))
    print_performance(pattern, patterns["Cross"])


def run_json_mode():
    data_path = Path(__file__).resolve().parent / "data.json"

    try:
        with data_path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {data_path}")
        return
    except json.JSONDecodeError as error:
        print(f"JSON 형식 오류: {error}")
        return
    except (OSError, UnicodeError) as error:
        print(f"파일을 읽을 수 없습니다: {error}")
        return

    if not isinstance(data, dict):
        print("데이터 형식 오류: 최상위 데이터는 객체여야 합니다.")
        return

    filters = data.get("filters")
    patterns = data.get("patterns")

    if not isinstance(filters, dict):
        print("데이터 형식 오류: filters는 객체여야 합니다.")
        return

    if not isinstance(patterns, dict):
        print("데이터 형식 오류: patterns는 객체여야 합니다.")
        return

    print("\nJSON 파일 로드 완료")
    print("필터 크기:", ", ".join(filters.keys()))
    print("전체 패턴 수:", len(patterns))

    total = len(patterns)
    passed = 0
    failures = []

    cross_3 = generate_patterns(3)["Cross"]

    performance_cases = {
        3: (cross_3, cross_3),
    }

    for case_id, case in patterns.items():
        try:
            if not isinstance(case, dict):
                raise ValueError("패턴 항목은 객체여야 합니다.")

            size = parse_case_size(case_id)
            expected = normalize_label(case.get("expected"))

            pattern = case.get("input")
            validate_matrix(pattern, size, "입력 패턴")

            filter_key = f"size_{size}"
            raw_filters = filters.get(filter_key)

            if not isinstance(raw_filters, dict):
                raise ValueError(f"{filter_key} 필터가 없거나 형식이 잘못되었습니다.")

            normalized_filters = {}

            for label, matrix in raw_filters.items():
                standard_label = normalize_label(label)

                if standard_label in normalized_filters:
                    raise ValueError(f"중복된 필터 라벨: {standard_label}")

                validate_matrix(matrix, size, f"{standard_label} 필터")
                normalized_filters[standard_label] = matrix

            if set(normalized_filters) != {"Cross", "X"}:
                raise ValueError("Cross와 X 필터가 모두 필요합니다.")

            score_cross = mac(pattern, normalized_filters["Cross"])
            score_x = mac(pattern, normalized_filters["X"])

        except (ValueError, OverflowError) as error:
            reason = str(error)
            failures.append((case_id, reason))
            print(f"{case_id}: FAIL — {reason}")
            continue

        if size not in performance_cases:
            performance_cases[size] = (
                pattern,
                normalized_filters["Cross"],
            )

        result = judge(score_cross, score_x, "Cross", "X")

        if result == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            reason = f"예상={expected}, 실제={result}"
            failures.append((case_id, reason))

        print(
            f"{case_id}: "
            f"Cross={score_cross:.10g}, "
            f"X={score_x:.10g}, "
            f"판정={result}, "
            f"expected={expected} → {status}"
        )

    print_json_performance(performance_cases)
    print_optimization_comparison(performance_cases)

    print("\n결과 요약")
    print(f"전체 테스트 수: {total}")
    print(f"통과 수: {passed}")
    print(f"실패 수: {len(failures)}")

    if failures:
        print("\n실패 케이스 목록")

        for case_id, reason in failures:
            print(f"- {case_id}: {reason}")
    else:
        print("실패 케이스 없음")

def main():
    while True:
        print("\nMini NPU 시뮬레이터")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 자동 생성 패턴으로 판정 및 성능 비교")

        choice = input("모드를 선택하세요 (1/2/3): ").strip()

        if choice == "1":
            run_manual_mode()
            break

        if choice == "2":
            run_json_mode()
            break

        if choice == "3":
            run_generated_mode()
            break

        print("입력 오류: 1, 2 또는 3을 입력하세요.")

if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 종료되어 프로그램을 마칩니다.")
