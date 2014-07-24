all: libpreload.so

libpreload.so: libpreload.c
	$(CC) -fPIC -shared -o $@ $< -ldl

clean:
	- rm libpreload.so
