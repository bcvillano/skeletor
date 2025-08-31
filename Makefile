DIRECTORY=bin
MAC=macos-agent.bin
LINUX=linux-agent.bin
WIN=windows-agent.exe
ARM=arm-agent.bin
BSD=bsd-agent.bin
FLAGS=-ldflags "-s -w"
WIN-FLAGS=-ldflags -H=windowsgui

all: clean create-directory agent-linux agent-windows agent-mac agent-fuckbsd agent-rasp

create-directory:
	mkdir ${DIRECTORY}

agent-mac:
	echo "Compiling macOS binary"
	env GOOS=darwin GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${MAC} ./client/go/main.go

agent-linux:
	echo "Compiling Linux binary"
	env GOOS=linux GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${LINUX} ./client/go/main.go

agent-windows:
	echo "Compiling Windows binary"
	env GOOS=windows GOARCH=amd64 go build ${WIN-FLAGS} -o ${DIRECTORY}/${WIN} ./client/go/main.go

agent-rasp:
	echo "Compiling ARM binary"
	env GOOS=linux GOARCH=arm GOARM=7 go build ${FLAGS} -o ${DIRECTORY}/${ARM} ./client/go/main.go

agent-freebsd:
	echo "Compiling FreeBSD binary"
	env GOOS=freebsd GOARCH=amd64 go build ${FLAGS} -o ${DIRECTORY}/${BSD} ./client/go/main.go

clean:
	rm -rf ${DIRECTORY}