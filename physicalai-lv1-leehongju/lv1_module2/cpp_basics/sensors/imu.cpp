#include "imu.hpp"

imu::imu(const std::string& name) : sensor(name) {
    std::cout << "[Imu Constructor] " << name << " created\n";
}

imu::~imu() {
    std::cout << "[Imu ~Destructor] " << name << " Derived destroyed\n";
}

double imu::read() {
    return 9.81; // 예시 가속도 데이터 (m/s^2)
}