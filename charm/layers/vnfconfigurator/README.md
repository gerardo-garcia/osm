# Overview

This is an example charm layer for vnf configuration designed to be used with
[OSM](https://osm.etsi.org).

This charm layer uses the vnfproxy layer, which, in turn, uses the sshproxy
layer. The layer provides the mechanism to ssh to the VNF and run some
commands. A simple example is shown in the action 'touch'.

There are two potential scenarios for this charm, either to manage directly
the VNF or to manage the EMS that, in turn, manages the VNF.

## Scenario 1: Direct management of VNF

The VNF does not need an EM to be managed, typically because it offers a
well known CLI or API that could be used from a charm.

The charm vnfconfigurator is associated to the VNF and can be used to do the
day-1 and day-2 configuration.

     +------------------------------+
     |                              |
     |    charm vnfconfigurator     |
     |                              |
     +--------------+---------------+
                    |
                    |
     +--------------v---------------+
     |                              |
     |             VNF              |
     |                              |
     +------------------------------+

The day-1 configuration is done through the action called "day1-configuration".
The implementation can be done in very different ways, but in all the cases
the parameters to be configured as part of the day-1 should be part of the
action.

Some of the options to create the day-1 configuration are the following:
- The charm has a template for day1 configuration and particularizes it with
the input parameters. Then the charm copies that configuration in the VNF
(e.g. SSH + echo commands, SCP, specific API/protocol, etc.), and tells the
VNF to apply it.
- The VNF has the template, the charm particularizes it remotely with the
input parameters (e.g. SSH + sed command), and tells the VNF to apply it.
- The full configuration file is in an external system. This assumes that the
configuration has been previously injected in that external system and can be
retrieved from the remote location with a specific URL. The configuration file
of each VNF should have a different URL, probably determined by the VNF name.
Then:
  - Either the charm tells the VNF to retrieve the configuration file
  - Or the charm gets the configuration file and pushes it to the VNF.

Every day2-operation is done through a specific action. As an example, an
action called "day2-operation" is included. Typically the action will connect
via ssh or another protocol to the VNF and execute some commands in the VNF.

## Scenario 2: Indirect management through an EM

The VNF relies on an EM to be managed, typically because it offers a
proprietary CLI or API only known by the EM.

The charm vnfconfigurator is associated to the EMS and can be used to do the
day-1 and day-2 configuration. In addition, there can be a second charm,
vnfconfiguratorclient, associated to the VNF, which can be used to pull the
day1-configuration from the EMS.

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

1. Modify the charm layer accordingly. The charm layer already defines three
Juju actions, _**touch**_, _**day1-configuration**_, and _**day2-operation**_.
You can optionally define additional actions if needed by your VNF.
Actions have to be defined in the file 'actions.yaml'. In addition, for each
action there needs to be a file in actions folder with the name of the action.
You can copy one of the existing files for that purpose.

2. Implement the code for the action. It has to be done in
'reactive/vnfconfigurator.py'. The code of the action 'touch' is functional,
while the code for the actions 'day1-configuration' and 'day2-operation'
is only a placeholder that has to be completed.

3. Build the charm, via the *charm build* command.

4. Update the VNF descriptor (VNFD) to use the charm:
  a) specify the name of the Juju charm in in the VNF configuration;
  b) Include the actions “touch", "day1-configuration" and "day2-operation",
    or the new ones as a service primitive or as an initial configuration primitive
    in the VNF descriptor.

5. Include the compiled charm in the VNF package.

More comprehensive and complementary information on building *Proxy charms*
can be found in the [OSM wiki](https://osm.etsi.org/wikipub/index.php/Creating_your_VNF_Charm)
and in the documentation of the [vnfproxy layer](https://github.com/AdamIsrael/vnfproxy).


