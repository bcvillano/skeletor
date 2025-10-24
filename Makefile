DIRECTORY=bin
MAC=macos-agent.bin
LINUX=linux-agent.bin
WIN=windows-agent.exe
ARM=arm-agent.bin
BSD=bsd-agent.bin
FLAGS=-ldflags "-s -w"
WIN-FLAGS=-ldflags "-s -w -H=windowsgui"
SOURCE=./implants/go
RESOURCES=./resources

all: clean create-directory agent-linux agent-mac agent-freebsd agent-rasp agent-windows

create-directory:
	mkdir ${DIRECTORY}

agent-mac:
	echo "Compiling macOS binary"
	env GOOS=darwin GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${MAC} ${SOURCE}

agent-linux:
	echo "Compiling Linux binary"
	env GOOS=linux GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${LINUX} ${SOURCE}

agent-windows:
	echo "Generating Windows resources"
	goversioninfo -o ${SOURCE}/resource.syso ${RESOURCES}/versioninfo.json
	echo "Compiling Windows binary"
	env GOOS=windows GOARCH=amd64 go build ${WIN-FLAGS} -o ${DIRECTORY}/${WIN} ${SOURCE}
	rm -f $(SOURCE)/resource.syso

agent-rasp:
	echo "Compiling ARM binary"
	env GOOS=linux GOARCH=arm GOARM=7 go build ${FLAGS} -o ${DIRECTORY}/${ARM} ${SOURCE}

agent-freebsd:
	echo "Compiling FreeBSD binary"
	env GOOS=freebsd GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${BSD} ${SOURCE}

clean:
	rm -rf ${DIRECTORY}