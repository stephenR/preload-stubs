all: libpreload.so

libpreload.so: libpreload.c
	$(CC) -std=c99 -fPIC -shared -o $@ $< -ldl

clean:
	- rm libpreload.so
