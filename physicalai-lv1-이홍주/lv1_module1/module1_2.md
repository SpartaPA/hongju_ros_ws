고른 접속 대상: localhost / 가상머신 중 ___ — 무비밀번호 접속 로그와 who·echo $SSH_CONNECTION 출력
개인키·공개키 중 서버에 등록하는 것: ___ — 안전한 이유
원격 단일 명령 실행과 scp 전송 출력
두 장치를 구분한 속성: 라이다 ___ / IMU ___
작성한 udev 규칙 2개 + 규칙 키 설명표
순서를 바꿔 재연결한 뒤 ls -l /dev/robot_* 결과
실제 USB 센서용 규칙 초안과 구분 근거


**내 서버 sshd를 설치 한다.(openssh)**
sudo apt install openssh-server

**active(running) 확인**
systemctl status ssh
```
ssh.service - OpenBSD Secure Shell server
     Loaded: loaded (/lib/systemd/system/ssh.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2026-08-25 09:00:28 KST; 26min ago
       Docs: man:sshd(8)
             man:sshd_config(5)
   Main PID: 1097 (sshd)
      Tasks: 1 (limit: 37548)
     Memory: 3.6M
        CPU: 10ms
     CGroup: /system.slice/ssh.service
             └─1097 "sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups"
```

**22번 포트 확인**
ss -tlnp | grep :22
```
LISTEN 0      128          0.0.0.0:22        0.0.0.0:*          
LISTEN 0      128             [::]:22           [::]:*
```

**localhost로 접속**
ssh 사용자@localhost
```
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-138-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

153 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm
```

키 페어 - 암호와 방식

**SSH키 생성**
ssh-keygen -t ed25519
```
SHA256:sjGLzUuk5A2aHTKX5psKtv26z+1+DLjBys7JdX3Jsco pa8@pa8-Legion-Pro-5-16IAX10
```

**키를 해당 서버에 등록**
ssh-copy-id 사용자@아이피
```
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/home/pa8/.ssh/id_ed25519.pub"
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
```

**서버에 등록하는 SSH는 공개키**
비대칭 암호화 특성상 공개키가 유출되어도 클라이언트에만 존재하는 비밀 개인키를 역산해 내는 것이 수학적으로 불가능하기 때문

**접속하지 않고 명령만 실행**
ssh 사용자@서버 'uname -a'
```
Linux pa8-Legion-Pro-5-16IAX10 6.8.0-138-generic #138~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Fri Aug  7 13:43:15 UTC  x86_64 x86_64 x86_64 GNU/Linux
```

**파일 복사**
scp 파일 사용자@아이피:절대위치
```
cp hi.txt pa8@localhost:/home/pa8/test/
hi.txt                                                                                   100%    0     0.0KB/s   00:00
```

**접속되어 있는 사용자 확인**
who
```pa8      tty2         2026-08-25 09:03 (tty2)```
echo $SSH_CONNECTION
```127.0.0.1 54668 127.0.0.1 22```

**시리얼 장치가 있는지 확인**
ls -l /dev/tty*
```
crw-rw-rw- 1 root tty     5,  0 Aug 25 10:02 /dev/tty
crw--w---- 1 root tty     4,  0 Aug 25 09:00 /dev/tty0
crw--w---- 1 root tty     4,  1 Aug 25 09:00 /dev/tty1
crw--w---- 1 root tty     4, 10 Aug 25 09:00 /dev/tty10
```

**가상 sensor 장치 생성**
mkdir -p ~/fake_sensors && cd ~/fake_sensors
**파일생성 10M 크기로**
truncate -s 10M lidar.img imu.img
**블록장치로 연결**
sudo losetup -f --show lidar.img
sudo losetup -f --show imu.img
```
/dev/loop22
/dev/loop23
```

**udev데몬의 단계별로 속성 출력**
udevadm info --attribute-walk /dev/loop(N)
```
looking at device '/devices/virtual/block/loop22':
    KERNEL=="loop22"
    SUBSYSTEM=="block"
    DRIVER==""
    ATTR{alignment_offset}=="0"
    ATTR{capability}=="0"
```

**규칙파일 수정**
/etc/udev/rules.d/99-robot-sensor.rules
```
# virtual robot sensor rules

# LiDAR
SUBSYSTEM=="block", KERNEL=="loop22", SYMLINK+="robot_lidar", MODE="0666"

# IMU
SUBSYSTEM=="block", KERNEL=="loop23", SYMLINK+="robot_imu", MODE="0666"
```

**장치 규칙**
| SUBSYSTEM | 장치가 속한 udev 서브시스템. 블록 장치=block, USB=tty                                                                         |
| --------- | --------------------------------------------------------------------------------------------------------------- |
| KERNEL    | 커널이 부여한 장치 이름 패턴을 조건으로 비교합니다.                                                                                   |
| ATTR{...} | sysfs의 장치 속성을 읽어 조건으로 비교하거나 값을 설정합니다. 실제 USB 센서는 ATTRS{idVendor}, ATTRS{idProduct}, ATTRS{serial}처럼 식별에 주로 씁니다. |
| SYMLINK   | 기존 장치는 유지하면서, 같은 장치를 가리키는 추가 심볼릭 링크.                                                                            |
| MODE      | 장치 파일의 권한을 설정합니다. 일반적으로 그룹에 읽기·쓰기 권한을 주기 위해 "0660"을 사용합니다.                                                      |
| GROUP     | 장치 파일의 소유 그룹을 설정합니다. 해당 그룹에 사용자를 넣으면 sudo 없이 장치에 접근하게 할 수 있습니다.                                                 |
| ==        | **비교 연산자**. 장치의 현재 속성이 오른쪽 값과 일치할 때만 규칙이 적용됩니다.                                                                 |
| =         | **값 설정 연산자**. 해당 키의 값을 지정합니다. 목록 성격의 키에서는 기존 값을 대체할 수 있습니다.                                                     |
| +=        | **추가 연산자**. 기존 값은 유지하고 새 항목을 덧붙입니다. SYMLINK에는 보통 이것을 사용합니다.                                                     |


**블록장치 고정이름 SYMLINK**
/dev/robot_lidar, /dev/robot_imu

**udev데몬 규칙 다시 읽기**
sudo udevadm control --reload-rules

**기존 장치 이벤트 재발생**
sudo udevadm trigger --subsystem-match=tty
(--subsystem-match : 해당 장치만)

ls -l /dev/robot_*
```
lrwxrwxrwx 1 root root 6 Aug 25 15:29 /dev/robot_imu -> loop23
lrwxrwxrwx 1 root root 6 Aug 25 15:29 /dev/robot_lidar -> loop22
```

**순서를 바꿔 재연결한 결과**
```
lrwxrwxrwx 1 root root 6 Aug 25 15:54 /dev/robot_imu -> loop23
lrwxrwxrwx 1 root root 6 Aug 25 15:54 /dev/robot_lidar -> loop22
```

**실제 USB 센서용 규칙 초안과 구분 근거**
```
# LiDAR
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="lidar", MODE="0666"

# IMU
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", SYMLINK+="imu", MODE="0666"
```
Vendor가 같아도 udev에서 (0403, 6001)조합과 (0403, 6015)조합으로 구분하여 링크 생성. Vendor와 product까지 같으면 serial번호로 구분한다.