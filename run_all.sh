#!/bin/bash
display_usage() {
    echo -e "launches u3etas post-processing."
    echo -e "\n\tusage: $0 dir [tag] \n"
}
if [[ ${#} -eq 0 ]]; then
    display_usage
    exit
fi
base_dir=$1
tag=$2
while IFS= read -r -d $'\0'; do
    name=$(dirname $REPLY | sed "s/\.\///g")
    dir="$base_dir"/"$(date +%Y-%m-%d)"/"$(date +%Y-%m-%d)"_"$name"$tag
    cd $(dirname $REPLY)
    echo -e launching $(basename $REPLY) "-> writing to $dir"
    sbatch $(basename $REPLY) $dir
    cd ..
done < <(find . -name "*.slurm" -print0)

