# Overview

This is an example charm layer for vnf configuration designed to be used with
[OSM](https://osm.etsi.org).

This is a VNF proxy charm for day1 configuration of a VNF. It assumes that the
day1 configuration resides in an external element, e.g. EM, and it is
retrieved by the VNF using a program that is inside the VNF.

This charm layer uses the vnfproxy layer, which, in turn, uses the sshproxy
layer. The layer provides the mechanism to ssh to the VNF and run some
commands. A simple example is shown in the action 'touch'.

The scenario for this charm assumes that the VNF is managed from an EMS,
typically because it offers a proprietary CLI or API only known by the EMS.
However, the EMS cannot inject the day1 config into the VNF, but requires
the VNF to retrieve it from the EMS.

The charm 'vnfconfiguratorclient' is associated to the VNF and is used to pull
the day1-configuration from the EMS. In addition, another charm like
'vnfconfigurator' can be associated to the EMS and can be used to create the
day-1 configuration and perform day-2 operations.

     +------------------------------+     +------------------------------+
     | charm vnfconfiguratorclient  |     |                              |
     |                              |     |    charm vnfconfigurator     |
     |          (optional)          |     |                              |
     +--------------+---------------+     +--------------+---------------+
                    |                                    |
  +-----------------|------------------------------------|------------------+
  | NS              |                                    |                  |
  |  +--------------v---------------+     +--------------v---------------+  |                 +----------+
  |  |                              |     |                              |  |   optionally    |          |
  |  |             VNF              |     |             EMS              <-------------------->   OSS    |
  |  |                              |     |                              |  |                 |          |
  |  +--------------------------+---+     +---+--------------------------+  |                 +----------+
  |                             |             |                             |
  |                             |   mgmt net  |                             |
  |                             +-------------+            	            |
  +-------------------------------------------------------------------------+


# Usage

As mentioned before, this charm layer includes the layer
[vnfproxy](https://github.com/AdamIsrael/vnfproxy). For more information on
*proxy charms*, the reader is referred to the [OSM wiki](https://osm.etsi.org/wikipub/index.php/Creating_your_VNF_Charm).

Step by step instructions to use this charm layer:

1. Modify the charm layer accordingly. The charm layer already defines two
Juju actions, _**touch**_, and _**get-day1-configuration**_.
You can optionally define additional actions if needed by your VNF.
Actions have to be defined in the file 'actions.yaml'. In addition, for each
action there needs to be a file in actions folder with the name of the action.
You can copy one of the existing files for that purpose.

2. Implement the code for the action. It has to be done in
'reactive/vnfconfiguratorclient.py'. The code of the action 'touch' is functional,
while the code for the actions 'get-day1-configuration' is only a placeholder
that has to be completed.

3. Build the charm, via the *charm build* command.

4. Update the VNF descriptor (VNFD) to use the charm:
  a) specify the name of the Juju charm in in the VNF configuration;
  b) Include the actions “touch", "get-day1-configuration",
    or the new ones as a service primitive or as an initial configuration primitive
    in the VNF descriptor.

5. Include the compiled charm in the VNF package.

More comprehensive and complementary information on building *Proxy charms*
can be found in the [OSM wiki](https://osm.etsi.org/wikipub/index.php/Creating_your_VNF_Charm)
and in the documentation of the [vnfproxy layer](https://github.com/AdamIsrael/vnfproxy).


