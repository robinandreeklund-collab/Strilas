# Host-paritetstest för den portabla C-kärnan (ingen ESP-IDF krävs).
#   make -C firmware-esp/test
CFLAGS = -O2 -Wall -I../components/strilas_core
test: core_test.c ../components/strilas_core/strilas_core.c
	cc $(CFLAGS) $^ -lm -o /tmp/strilas_core_test && /tmp/strilas_core_test
.PHONY: test
