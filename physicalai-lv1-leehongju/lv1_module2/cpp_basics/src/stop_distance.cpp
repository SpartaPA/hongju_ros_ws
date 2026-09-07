// stop_distance.cpp — 로봇의 제동(정지) 거리 계산 //
// 물리: 바퀴와 바닥 사이 마찰이 유일한 제동력이라고 보면
// 감속도 a = mu g (mu: 마찰계수, g: 중력가속도)
// 운동에너지 (1/2)m v^2 이 마찰일 (mu m g d) 로 모두 소모되어 정지하므로
// d = v^2 / (2 mu * g) //
// 빌드: g++ -Wall -Wextra -std=c++17 stop_distance.cpp -o stop_distance
// 실행: ./stop_distance <속도[m/s]> <마찰계수>
// 인자를 안 주면 값을 직접 입력받는다.

#include <iostream>
#include <iomanip>
#include <cstdlib>
#include <string>

// 중력가속도 상수 (m/s^2)
constexpr double GRAVITY = 9.8;

// 제동 거리 계산 함수: d = v^2 / (2 mu g)
double calculate_stop_distance(double speed, double friction) {
    if (friction <= 0.0)
    {
        return -1.0;
    }
    return (speed * speed) / (2.0 * friction * GRAVITY);
}

int main(int argc, char *argv[]) {
    double speed = 0.0;
    double friction = 0.0;

    // 명령줄 인자가 2개 이상 주어진 경우: ./stop_distance <속도> <마찰계수>
    if (argc >= 3) {
        try {
            speed = std::stod(argv[1]);
            friction = std::stod(argv[2]);
        }
        catch (const std::exception &e) {
            std::cerr << "[오류] 인자 변환 실패: 유효한 숫자를 입력해주세요.\n";
            std::cerr << "사용법: " << argv[0] << " <속도[m/s]> <마찰계수>\n";
            return 1;
        }
    }
    else {
        // 인자가 주어지지 않은 경우 직접 입력받기
        std::cout << "====== 로봇의 제동(정지) 거리 계산 ======\n";

        std::cout << "속도를 입력하세요 [m/s]: ";
        if (!(std::cin >> speed)) {
            std::cerr << "[오류] 올바른 속도 값을 입력해주세요.\n";
            return 1;
        }

        std::cout << "마찰계수를 입력하세요: ";
        if (!(std::cin >> friction)) {
            std::cerr << "[오류] 올바른 마찰계수 값을 입력해주세요.\n";
            return 1;
        }
    }

    // 유효성 검증
    if (speed < 0.0) {
        std::cerr << "[오류] 속도는 0 이상이어야 합니다.\n";
        return 1;
    }
    if (friction <= 0.0) {
        std::cerr << "[오류] 마찰계수는 0보다 커야 합니다.\n";
        return 1;
    }

    double distance = calculate_stop_distance(speed, friction);

    std::cout << "\n========================================\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "▶ 입력 속도 : " << speed << " m/s (" << (speed * 3.6) << " km/h)\n";
    std::cout << "▶ 마찰계수 : " << friction << "\n";
    std::cout << "▶ 중력가속도 : " << GRAVITY << " m/s²\n";
    std::cout << "----------------------------------------\n";
    std::cout << "▶ 계산된 제동거리: " << distance << " m\n";
    std::cout << "========================================\n";

    return 0;
}