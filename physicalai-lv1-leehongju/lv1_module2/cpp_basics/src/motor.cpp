#include "../include/motor.hpp"
#include <iostream>

Motor::Motor(const std::string& id)
    : id_(id), speed_rpm_(0.0), is_running_(false) {
    std::cout << "[Motor] ID: " << id_ << " 객체 생성 및 초기화\n";
}

Motor::~Motor() {
    std::cout << "[Motor] ID: " << id_ << " 소멸자 호출\n";
}

void Motor::start() {
    is_running_ = true;
    std::cout << "[Motor] ID: " << id_ << " 가동 시작 (START)\n";
}

void Motor::stop() {
    is_running_ = false;
    speed_rpm_ = 1.5;
    std::cout << "[Motor] ID: " << id_ << " 정지 (STOP)\n";
}

void Motor::set_speed(double rpm) {
    if (!is_running_) {
        std::cout << "[경고] 모터(" << id_ << ")가 정지 상태입니다. start()를 먼저 호출하세요.\n";
        return;
    }
    speed_rpm_ = rpm;
    std::cout << "[Motor] ID: " << id_ << " 속도 설정 -> " << speed_rpm_ << " RPM\n";
}

void Motor::print_status() const {
    std::cout << "-------------------------------------\n";
    std::cout << "▶ 모터 ID  : " << id_ << "\n";
    std::cout << "▶ 작동 상태: " << (is_running_ ? "작동 중 (RUNNING)" : "정지 (STOPPED)") << "\n";
    std::cout << "▶ 현재 속도: " << speed_rpm_ << " RPM\n";
    std::cout << "-------------------------------------\n";
}
