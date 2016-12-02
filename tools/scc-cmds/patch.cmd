# take a patch file, and make sure it is relative to where the patch.queue is
# being written. This is a standard requirement for most patch managers .. and
# it just makes life easier
patch() {
    local patch_name=$1
    local simple_patch_name=$(basename ${patch_name})

    if [ -n "${verbose}" ]; then
        echo "patch: $1 [${cbranch_name}]" >&2
    fi

    if [ ! -d "${outdir}/patches/${cbranch_name}" ]; then
        mkdir -p "${outdir}/patches/${cbranch_name}"
    fi

    relative_patch_name=${patch_name}
    relative_patch_dir=""
    if [ -n "${prefix}" ]; then
        relative_patch_name=$(echo ${relative_patch_name} | sed "s%${prefix}%%")
        relative_patch_dir=$(dirname ${relative_patch_name})
        mkdir -p ${outdir}/patches/${cbranch_name}/${relative_patch_dir}
    fi

    # we could compare the source and dest, and either warn or clobber, but for now, we just clobber
    cp -f "$patch_name" "${outdir}/patches/${cbranch_name}/${relative_patch_dir}"

    # output to the global and branch specific queue
    eval echo "\"patches/${cbranch_name}/${relative_patch_dir}/${simple_patch_name}\"" >> "${patchqueue}"
    if [ -n "${branch_patch_queue}" ]; then
       eval echo "\"patches/${cbranch_name}/${relative_patch_dir}/${simple_patch_name}\"" >> "${branch_patch_queue}"
    fi
    # outfile_append is the meta-series
    eval echo "\"patch patches/${cbranch_name}/${relative_patch_dir}/${simple_patch_name}\"" $outfile_append
}
