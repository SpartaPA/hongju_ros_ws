#ifndef SENSOR_HPP
#define SENSOR_HPP

#include <string>
#include <iostream>

// 값 범위 제한 함수 템플릿
template <typename T>
T clamp(T val, T low, T high) {
    if (val < low) return low;
    if (val > high) return high;
    return val;
}

class sensor {
protected:
    std::string name;

public:
    sensor(const std::string& name);
    
    // 가상 소멸자 선언
    virtual ~sensor();

    virtual double read() = 0; // 순수 가상 함수
    std::string getName() const;
};

#endif // SENSOR_HPP