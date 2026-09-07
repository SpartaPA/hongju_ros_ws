#include "lidar.hpp"

lidar::lidar(const std::string& name) : sensor(name) {
    buffer = new double[100]; // 자원 할당
    std::cout << "[Lidar Constructor] " << name << " created\n";
}

lidar::~lidar() {
    delete[] buffer; // 자원 해제
    std::cout << "[Lidar ~Destructor] " << name << " Derived destroyed (Buffer freed)\n";
}

double lidar::read() {
    return 0.42; // 예시 거리 데이터 (m)
}