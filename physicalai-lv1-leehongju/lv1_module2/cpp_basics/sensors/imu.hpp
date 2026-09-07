#ifndef IMU_HPP
#define IMU_HPP

#include "sensor.hpp"

class imu : public sensor {
public:
    imu(const std::string& name);
    ~imu() override;

    double read() override;
};

#endif // IMU_HPP