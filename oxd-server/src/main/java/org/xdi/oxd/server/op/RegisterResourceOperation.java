package org.xdi.oxd.server.op;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.xdi.oxauth.client.uma.ResourceSetRegistrationService;
import org.xdi.oxauth.client.uma.UmaClientFactory;
import org.xdi.oxauth.model.uma.MetadataConfiguration;
import org.xdi.oxauth.model.uma.ResourceSet;
import org.xdi.oxauth.model.uma.ResourceSetStatus;
import org.xdi.oxd.common.Command;
import org.xdi.oxd.common.CommandResponse;
import org.xdi.oxd.common.params.RegisterResourceParams;
import org.xdi.oxd.common.response.RegisterResourceOpResponse;
import org.xdi.oxd.server.DiscoveryService;
import org.xdi.oxd.server.HttpService;

/**
 * @author Yuriy Zabrovarnyy
 * @version 0.9, 09/08/2013
 */

public class RegisterResourceOperation extends BaseOperation {

    private static final Logger LOG = LoggerFactory.getLogger(RegisterResourceOperation.class);

    protected RegisterResourceOperation(Command p_command) {
        super(p_command);
    }

    @Override
    public CommandResponse execute() {
        try {
            final RegisterResourceParams params = asParams(RegisterResourceParams.class);
            if (params != null) {
                final MetadataConfiguration umaDiscovery = DiscoveryService.getInstance().getUmaDiscovery(params.getUmaDiscoveryUrl());
                final ResourceSetRegistrationService registrationService = UmaClientFactory.instance().createResourceSetRegistrationService(umaDiscovery, HttpService.getInstance().getClientExecutor());

                final ResourceSet resourceSet = new ResourceSet();
                resourceSet.setName(params.getName());
                resourceSet.setScopes(params.getScopes());

                final String id = String.valueOf(System.currentTimeMillis()); // most probably oxauth will ignore this id and will generate own one
                final ResourceSetStatus addResponse = registrationService.addResourceSet("Bearer " + params.getPatToken(), id, resourceSet);

                if (addResponse != null) {
                    final RegisterResourceOpResponse opResponse = new RegisterResourceOpResponse();
                    opResponse.setId(addResponse.getId());
                    opResponse.setRev(addResponse.getRev());
                    return okResponse(opResponse);
                } else {
                    LOG.error("No response on addResourceSet call from OP.");
                }
            }
        } catch (Exception e) {
            LOG.error(e.getMessage(), e);
        }
        return CommandResponse.INTERNAL_ERROR_RESPONSE;
    }
}
