TEMPLATE = subdirs
SUBDIRS += auto

isEmpty(QT_BASE_DIR) {
    error("Environment variable CAMCOPS_QT5_BASE_DIR is undefined")
}

message("From environment variable CAMCOPS_QT5_BASE_DIR, using custom Qt/library base directory: $${QT_BASE_DIR}")
message("... Qt version: $$[QT_VERSION]")
message("... CamCOPS src is at: $${CAMCOPS_SRC}")
message("... Eigen version: $${EIGEN_VERSION}")
