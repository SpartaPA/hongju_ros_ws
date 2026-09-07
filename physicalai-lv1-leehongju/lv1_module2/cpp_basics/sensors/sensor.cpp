#include "sensor.hpp"

sensor::sensor(const std::string& name) : name(name) {}

sensor::~sensor() {
    std::cout << "[Sensor ~Destructor] " << name << " Base destroyed\n";
}

std::string sensor::getName() const {
    return name;
}