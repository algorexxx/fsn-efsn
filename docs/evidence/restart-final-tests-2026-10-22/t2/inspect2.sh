cd /home/rehearsal/efsn-tools-union
git status --short | head
ls tests/restart/ | tr '\n' ' '; echo
grep -n "jumpTime\|ticketEnd" tests/restart/fixture_test.go
grep -rn "func Test" tests/restart/*.go | awk -F: '{print $1": "$3}' | head -60
ls tests/restart/testdata
ps -eo pid,etime,pcpu,rss,user,args --sort=-pcpu | head -5
cat /home/rehearsal/t1/* 2>/dev/null | head -20; ls -la /home/rehearsal/t1
