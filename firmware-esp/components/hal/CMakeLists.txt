idf_component_register(
    SRCS "hal_esp.c" "hal_msg.c"
    INCLUDE_DIRS "include"
    REQUIRES strilas_core esp_now esp_timer driver)
