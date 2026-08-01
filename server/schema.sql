CREATE DATABASE pulsegrid CHARACTER SET UTF8MB4 COLLATE UTF8MB4_UNICODE_CI;

CREATE TABLE device_metrics_history (
	 id 		    BIGINT AUTO_INCREMENT PRIMARY KEY,
	 device_id   VARCHAR(50) NOT NULL,
	 recorded_at DATETIME NOT NULL,
	 cpu_usage	 FLOAT NULL,
	 cpu_temp	 FLOAT NULL,
	 cpu_power	 FLOAT NULL,		   -- ⭐ Task 6.5-5(M6.5) 추가
	 gpu_usage	 FLOAT NULL,
	 gpu_temp	 FLOAT NULL,
	 gpu_power	 FLOAT NULL,		   -- ⭐ Task 6.5-5(M6.5) 추가	
	 ram_usage	 FLOAT NULL,
	 disk_usage	 FLOAT NULL,
	 disk_temp	 FLOAT NULL,
	 battery_level FLOAT NULL,         -- ⭐ Task 6-3(M6) 추가
	 battery_charging BOOLEAN NULL,    -- ⭐ Task 6-3(M6) 추가
	 
	 INDEX idx_device_time (device_id, recorded_at)		  
);
