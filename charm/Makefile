BUILD_DIR = .

CHARMS:= vnfconfigurator\
         vnfconfiguratorclient \
	 testmetrics
CHARM_SRC_DIR := layers
CHARM_BUILD_DIR := $(BUILD_DIR)/builds

CHARM_SRC_DIRS := $(addprefix $(CHARM_SRC_DIR)/, $(CHARMS))
CHARM_BUILD_DIRS := $(addprefix $(CHARM_BUILD_DIR)/, $(CHARMS))

all: $(CHARM_BUILD_DIRS)

clean:
	-@ $(RM) -rf $(CHARM_BUILD_DIR)

$(CHARM_BUILD_DIR)/%: $(CHARM_SRC_DIR)/%
	charm build -o $(BUILD_DIR) $<
