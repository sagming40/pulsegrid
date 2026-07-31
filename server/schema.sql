CREATE DATABASE pulsegrid CHARACTER SET UTF8MB4 COLLATE UTF8MB4_UNICODE_CI;

CREATE TABLE device_metrics_history (
	 id 		    BIGINT AUTO_INCREMENT PRIMARY KEY,
	 device_id   VARCHAR(50) NOT NULL,
	 recorded_at DATETIME NOT NULL,
	 cpu_usage	 FLOAT NULL,
	 cpu_temp	 FLOAT NULL,
	 gpu_usage	 FLOAT NULL,
	 gpu_temp	 FLOAT NULL,
	 ram_usage	 FLOAT NULL,
	 disk_usage	 FLOAT NULL,
	 disk_temp	 FLOAT NULL,
	 
	 INDEX idx_device_time (device_id, recorded_at)		  
);
