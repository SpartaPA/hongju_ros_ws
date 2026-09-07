#ifndef MOTOR_HPP
#define MOTOR_HPP

#include <string>

class Motor {
private:
    std::string id_;
    double speed_rpm_;
    bool is_running_;

public:
    // 생성자 및 소멸자
    Motor(const std::string& id);
    ~Motor();

    // 모터 제어 메서드
    void start();
    void stop();
    void set_speed(double rpm);
    void print_status() const;
};

#endif
