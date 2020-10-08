/*
 * Janssen Project software is available under the MIT License (2008). See http://opensource.org/licenses/MIT for full text.
 *
 * Copyright (c) 2020, Janssen Project
 */

package org.gluu.oxauth.comp;

import io.jans.as.model.common.IdType;
import org.apache.commons.lang.StringUtils;
import org.gluu.oxauth.BaseComponentTest;
import io.jans.as.server.idgen.ws.rs.InumGenerator;
import org.testng.Assert;
import org.testng.annotations.Test;

import javax.inject.Inject;

/**
 * @author Yuriy Zabrovarnyy
 * @version 0.9, 26/06/2013
 */

public class InumGeneratorTest extends BaseComponentTest {

	@Inject
	private InumGenerator inumGenerator;

	@Test
	public void test() {
		final String inum = inumGenerator.generateId(IdType.CLIENTS, "@!1111");
		Assert.assertTrue(StringUtils.isNotBlank(inum));
	}

}
