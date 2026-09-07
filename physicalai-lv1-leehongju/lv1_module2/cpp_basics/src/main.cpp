#include "../include/motor.hpp"
#include <iostream>

int main() {
    std::cout << "=====================================\n";
    std::cout << "       모터 제어 프로그램 시작        \n";
    std::cout << "=====================================\n";

    // Motor 객체 생성
    Motor my_motor("BLDC-01");
    my_motor.print_status();

    // 정지 상태에서 속도 변경 시도
    my_motor.set_speed(1000.0);

    // 모터 가동 및 속도 설정
    my_motor.start();
    my_motor.set_speed(2500.0);
    my_motor.print_status();

    // 모터 정지
    my_motor.stop();
    my_motor.print_status();

    std::cout << "=====================================\n";
    std::cout << "       모터 제어 프로그램 종료        \n";
    std::cout << "=====================================\n";

    return 0;
}
