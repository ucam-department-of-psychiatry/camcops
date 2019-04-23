..  docs/source/administrator/server_upgrading.rst

..  Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

Upgrading a CamCOPS server
==========================

This involves two steps: upgrading CamCOPS itself, then upgrading the CamCOPS
server database(s).


Upgrade the CamCOPS software
----------------------------

For Debian/Ubuntu:

.. code-block:: bash

    #!/bin/bash

    export CAMCOPS_VERSION=2.3.1  # ... choose a version here
    export CAMCOPS_PACKAGE_NAME=camcops-server_${CAMCOPS_VERSION}-1_all.deb
    wget https://egret.psychol.cam.ac.uk/camcops/download/linux_server/${CAMCOPS_PACKAGE_NAME}  # download

    sudo apt-get --yes remove camcops-server
    sudo gdebi --non-interactive ${CAMCOPS_PACKAGE_NAME}

For CentOS:

.. code-block:: bash

    #!/bin/bash

    export CAMCOPS_VERSION=2.3.1  # ... choose a version here
    export CAMCOPS_PACKAGE_NAME=camcops-server_${CAMCOPS_VERSION}-2.noarch.rpm
    wget https://egret.psychol.cam.ac.uk/camcops/download/linux_server/${CAMCOPS_PACKAGE_NAME}  # download

    sudo yum --assumeyes remove camcops-server  # remove old version
    sudo yum --assumeyes --verbose --rpmverbosity=DEBUG install ${CAMCOPS_PACKAGE_NAME}  # install new version


Upgrade the CamCOPS database
----------------------------

.. code-block:: bash

    # For example:
    sudo camcops_server upgrade_db --config /etc/camcops/camcops.conf

    # Notes:
    # - "sudo" only so that CamCOPS can read the config file
    # - Use your installation-specific config file!

For more detail, see :ref:`camcops_server <camcops_cli>`.
