CREATE DATABASE IF NOT EXISTS hanuman_travels
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hanuman_travels;

CREATE TABLE IF NOT EXISTS customer_bookings (
    booking_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(254) NULL,
    pickup VARCHAR(200) NULL,
    destination VARCHAR(200) NOT NULL,
    travel_date DATE NULL,
    trip_type ENUM('Local', 'Outstation', 'Airport', 'Family', 'Corporate')
        NOT NULL DEFAULT 'Local',
    car_type VARCHAR(80) NOT NULL DEFAULT 'Baleno',
    passengers TINYINT UNSIGNED NOT NULL DEFAULT 1,
    requirements TEXT NULL,
    booking_status ENUM('New', 'Contacted', 'Confirmed', 'Completed', 'Cancelled')
        NOT NULL DEFAULT 'New',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_id),
    INDEX idx_customer_bookings_phone (phone),
    INDEX idx_customer_bookings_travel_date (travel_date),
    INDEX idx_customer_bookings_status (booking_status),
    CONSTRAINT chk_customer_bookings_passengers
        CHECK (passengers BETWEEN 1 AND 8)
) ENGINE=InnoDB;
