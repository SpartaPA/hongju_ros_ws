#include <iostream>
#include <vector>
#include <memory>
#include <unordered_map>
#include <algorithm>

#include "sensor.hpp"
#include "lidar.hpp"
#include "imu.hpp"

// 메모리 누수 재현 함수 (AddressSanitizer 테스트용)
void causeMemoryLeak() {
    sensor* leakedSensor = new lidar("LeakedLidar");
    (void)leakedSensor->read();
    // delete leakedSensor; // Intentional Leak
}

// RAII를 적용한 메모리 누수 해결 함수
void fixMemoryLeak() {
    auto safeSensor = std::make_unique<lidar>("SafeLidar");
    (void)safeSensor->read();
} // 스코프를 벗어나며 std::unique_ptr에 의해 자동 해제

int main() {
    std::cout << "=== 스택 vs 힙 객체 수명 관찰 ===\n";
    {
        std::cout << "-- 스택 객체 생성 --\n";
        imu stackImu("Stack_IMU");
        
        std::cout << "-- 힙 객체 생성 (make_unique) --\n";
        auto heapLidar = std::make_unique<lidar>("Heap_Lidar");
        
        std::cout << "-- Scope 종료 직전 --\n";
    }
    std::cout << "-- Scope 종료 완료 --\n\n";

    std::cout << "=== 2. 다형성 루프 출력 ===\n";
    std::vector<std::unique_ptr<sensor>> sensors;
    sensors.push_back(std::make_unique<lidar>("Front_Lidar"));
    sensors.push_back(std::make_unique<imu>("Center_IMU"));

    for (const auto& sensor : sensors) {
        std::cout << sensor->getName() << " Read Value: " << sensor->read() << "\n";
    }
    std::cout << "\n";

    std::cout << "=== STL 및 알고리즘 활용 (unordered_map & count_if) ===\n";
    std::unordered_map<std::string, double> latest_readings;
    latest_readings["Front_Lidar"] = sensors[0]->read();
    latest_readings["Center_IMU"] = sensors[1]->read();

    std::vector<double> distance_logs = {0.12, 0.48, 0.85, 0.33, 1.20, 0.05, 0.50, 0.51};
    
    int count = std::count_if(distance_logs.begin(), distance_logs.end(), [](double dist) {
        return dist <= 0.35;
    });
    std::cout << "거리가 0.35 이내인 기록 개수: " << count << "개\n\n";

    std::cout << "=== Clamp 템플릿 적용 ===\n";
    double speed = clamp(120.5, 0.0, 100.0);
    int pixel = clamp(280, 0, 255);
    std::cout << "Clamped Speed: " << speed << " (Max: 100.0)\n";
    std::cout << "Clamped Pixel: " << pixel << " (Max: 255)\n\n";

    std::cout << "=== 메모리 누수 테스트 실행 ===\n";
    // causeMemoryLeak(); // 누수 검출 테스트 시 주석 해제
    fixMemoryLeak();

    return 0;
}