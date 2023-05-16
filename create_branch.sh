
switch=$1

if [ -z "$switch" ]; then
    echo "use ./create_branch -do"
else
    cp Step01/* Step00
    cp Step02/* Step01
    cp Step03/* Step02
    cp Step04/* Step03
    cp Step05/* Step04
    cp Step06/* Step05
    cp Step07/* Step06
    cp Step08/* Step07
    cp Step09/* Step08
    cp Step10/* Step09
    cp Step11/* Step10
fi
