DIRECTORY=bin
MAC=macos-agent.bin
LINUX=linux-agent.bin
WIN=windows-agent.exe
ARM=arm-agent.bin
BSD=bsd-agent.bin
WIN-DEBUG=windebug.exe
FLAGS=-ldflags "-s -w"
WIN-FLAGS=-ldflags "-s -w -H=windowsgui"
WIN-DEBUG-FLAGS=-ldflags "-s -w"
SOURCE=./implants/go
RESOURCES=./resources

all: clean create-directory linux mac freebsd arm windows
comp: clean linux freebsd windows

create-directory:
	mkdir ${DIRECTORY}

mac:
	echo "Compiling macOS binary"
	env GOOS=darwin GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${MAC} ${SOURCE}

linux:
	echo "Compiling Linux binary"
	env GOOS=linux GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${LINUX} ${SOURCE}

windows:
	echo "Generating Windows resources"
	goversioninfo -o ${SOURCE}/resource.syso ${RESOURCES}/versioninfo.json
	echo "Compiling Windows binary"
	env GOOS=windows GOARCH=amd64 go build ${WIN-FLAGS} -o ${DIRECTORY}/${WIN} ${SOURCE}
	rm -f $(SOURCE)/resource.syso

win-debug:
	env GOOS=windows GOARCH=amd64 go build ${WIN-DEBUG-FLAGS} -o ${DIRECTORY}/${WIN-DEBUG} ${SOURCE}

arm:
	echo "Compiling ARM binary"
	env GOOS=linux GOARCH=arm GOARM=7 go build ${FLAGS} -o ${DIRECTORY}/${ARM} ${SOURCE}

freebsd:
	echo "Compiling FreeBSD binary"
	env GOOS=freebsd GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${BSD} ${SOURCE}

clean:
	rm -rf ${DIRECTORY}