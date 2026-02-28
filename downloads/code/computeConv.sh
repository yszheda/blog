#!/bin/bash
declare -i i=0
declare -i j=1
while [ $i -le 7 ]
do
awk 'NR==FNR{a[$1]=$NF}
NR>FNR&&a[$1]>$NF{print $1"\t"a[$1]-$NF}
NR>FNR&&a[$1]<$NF{print $1"\t"$NF-a[$1]}' rank-10G-10-1R-n_$i-sort/part-00000 rank-10G-10-1R-n_$j-sort/part-00000 > diff_$i
let "i += 1"
let "j += 1"
done
awk 'NR==FNR{a[$1]=$NF}
NR>FNR&&a[$1]>$NF{print $1"\t"a[$1]-$NF}
NR>FNR&&a[$1]<$NF{print $1"\t"$NF-a[$1]}' rank-10G-10-1R-n_8-sort/part-00000 rank-10G-10-1R-sort/part-00000 > diff_8
rm diff-sum
touch diff-sum
let "i = 0"
while [ $i -le 8 ]
do
		cat diff_$i | awk '{sum+=$NF} END {print sum}' >> diff-sum
		let "i += 1"
done

