cd /home/rehearsal
ls -la
for d in efsn-final efsn-tools-union; do echo "== $d"; git -C $d log --oneline -5; git -C $d status --short | head; done
ls -la final-bin
sha256sum final-bin/* 2>/dev/null
df -h / /mnt/w
free -m
ps -eo pid,etime,pcpu,rss,user,args --sort=-rss | head -8
losetup -a 2>/dev/null
