#ifndef LIDAR_HPP
#define LIDAR_HPP

#include "sensor.hpp"

class lidar : public sensor {
private:
    double* buffer; // 동적 할당 자원 (가상 소멸자 테스트용)

public:
    lidar(const std::string& name);
    ~lidar() override;

    double read() override;
};

#endif // LIDAR_HPP