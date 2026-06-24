idf_component_register(
    SRCS "strilas_main.c" "node_optik.c" "node_target.c"
    INCLUDE_DIRS "."
    REQUIRES strilas_core hal)
# nod-roll: -DSTRILAS_ROLE=0|1|2 (default optik)
if(DEFINED STRILAS_ROLE)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE STRILAS_ROLE=${STRILAS_ROLE})
endif()
