/*
 * oxAuth is available under the MIT License (2008). See http://opensource.org/licenses/MIT for full text.
 *
 * Copyright (c) 2014, Gluu
 */

package org.gluu.oxauth.service;

import com.google.common.collect.Lists;
import org.apache.commons.lang.StringUtils;
import org.gluu.oxauth.model.config.StaticConfiguration;
import org.gluu.oxauth.model.configuration.AppConfiguration;
import io.jans.orm.PersistenceEntryManager;
import org.gluu.search.filter.Filter;
import org.gluu.service.BaseCacheService;
import org.gluu.service.CacheService;
import org.gluu.service.LocalCacheService;
import io.jans.util.StringHelper;
import org.oxauth.persistence.model.Scope;
import org.slf4j.Logger;

import javax.ejb.Stateless;
import javax.inject.Inject;
import javax.inject.Named;
import java.util.ArrayList;
import java.util.List;

/**
 * @author Javier Rojas Blum Date: 07.05.2012
 * @author Yuriy Movchan Date: 2016/04/26
 */
@Stateless
@Named
public class ScopeService {

    @Inject
    private Logger log;

    @Inject
	private AppConfiguration appConfiguration;

	@Inject
	private CacheService cacheService;

    @Inject
    private LocalCacheService localCacheService;

    @Inject
    private PersistenceEntryManager ldapEntryManager;

    @Inject
    private StaticConfiguration staticConfiguration;

    /**
     * returns a list of all scopes
     *
     * @return list of scopes
     */
    public List<Scope> getAllScopesList() {
        String scopesBaseDN = staticConfiguration.getBaseDn().getScopes();

        return ldapEntryManager.findEntries(scopesBaseDN,
                Scope.class,
                Filter.createPresenceFilter("inum"));
    }

    public List<String> getDefaultScopesDn() {
        List<String> defaultScopes = new ArrayList<>();

        for (Scope scope : getAllScopesList()) {
            if (Boolean.TRUE.equals(scope.isDefaultScope())) {
                defaultScopes.add(scope.getDn());
            }
        }

        return defaultScopes;
    }

    public List<String> getScopesDn(List<String> scopeNames) {
        List<String> scopes = new ArrayList<>();

        for (String scopeName : scopeNames) {
            Scope scope = getScopeById(scopeName);
            if (scope != null) {
                scopes.add(scope.getDn());
            }
        }

        return scopes;
    }

    public List<String> getScopeIdsByDns(List<String> dns) {
        List<String> names = Lists.newArrayList();
        if (dns == null || dns.isEmpty()) {
            return dns;
        }

        for (String dn : dns) {
            Scope scope = getScopeByDnSilently(dn);
            if (scope != null && StringUtils.isNotBlank(scope.getId())) {
                names.add(scope.getId());
            }
        }
        return names;
    }

    /**
     * returns Scope by Dn
     *
     * @return Scope
     */
    public Scope getScopeByDn(String dn) {
    	BaseCacheService usedCacheService = getCacheService();
        final Scope scope = usedCacheService.getWithPut(dn, () -> ldapEntryManager.find(Scope.class, dn), 60);
        if (scope != null && StringUtils.isNotBlank(scope.getId())) {
        	usedCacheService.put(scope.getId(), scope); // put also by id, since we call it by id and dn
        }
        return scope;
    }

    /**
     * returns Scope by Dn
     *
     * @return Scope
     */
    public Scope getScopeByDnSilently(String dn) {
        try {
            return getScopeByDn(dn);
        } catch (Exception e) {
            log.trace(e.getMessage(), e);
            return null;
        }
    }

    /**
     * Get scope by DisplayName
     *
     * @param id
     * @return scope
     */
    public Scope getScopeById(String id) {
    	BaseCacheService usedCacheService = getCacheService();

    	final Object cached = usedCacheService.get(id);
        if (cached != null)
            return (Scope) cached;

        try {
            List<Scope> scopes = ldapEntryManager.findEntries(
                    staticConfiguration.getBaseDn().getScopes(), Scope.class, Filter.createEqualityFilter("oxId", id));
            if ((scopes != null) && (scopes.size() > 0)) {
                final Scope scope = scopes.get(0);
                usedCacheService.put(id, scope);
                usedCacheService.put(scope.getDn(), scope);
                return scope;
            }
        } catch (Exception e) {
            log.error("Failed to find scope with id: " + id, e);
        }
        return null;
    }
    
    /**
     * Get scope by oxAuthClaims
     *
     * @param claimDn
     * @return List of scope
     */
    public List<Scope> getScopeByClaim(String claimDn) {
    	List<Scope> scopes = fromCacheByClaimDn(claimDn);
    	if (scopes == null) {
	        Filter filter = Filter.createEqualityFilter("oxAuthClaim", claimDn);
	        
	    	String scopesBaseDN = staticConfiguration.getBaseDn().getScopes();
	        scopes = ldapEntryManager.findEntries(scopesBaseDN, Scope.class, filter);
	
	        putInCache(claimDn, scopes);
    	}

        return scopes;
    }

	public List<Scope> getScopesByClaim(List<Scope> scopes, String claimDn) {
		List<Scope> result = new ArrayList<>();
		for (Scope scope : scopes) {
			List<String> claims = scope.getOxAuthClaims();
			if ((claims != null) && claims.contains(claimDn)) {
				result.add(scope);
			}
		}

		return result;
	}

    private void putInCache(String claimDn, List<Scope> scopes) {
    	if (scopes == null) {
    		return;
    	}

    	BaseCacheService usedCacheService = getCacheService();
    	try {
        	String key = getClaimDnCacheKey(claimDn);
        	usedCacheService.put(key, scopes);
        } catch (Exception ex) {
            log.error("Failed to put scopes in cache, claimDn: '{}'", claimDn, ex);
        }
    }

    @SuppressWarnings("unchecked")
	private List<Scope> fromCacheByClaimDn(String claimDn) {
    	BaseCacheService usedCacheService = getCacheService();
        try {
        	String key = getClaimDnCacheKey(claimDn);
            return (List<Scope>) usedCacheService.get(key);
        } catch (Exception ex) {
            log.error("Failed to get scopes from cache, claimDn: '{}'", claimDn, ex);
            return null;
        }
    }

    private static String getClaimDnCacheKey(String claimDn) {
        return "claim_dn" + StringHelper.toLowerCase(claimDn);
    }

    public void persist(Scope scope) {
        ldapEntryManager.persist(scope);
    }

    private BaseCacheService getCacheService() {
    	if (appConfiguration.getUseLocalCache()) {
    		return localCacheService;
    	}
    	
    	return cacheService;
    }

}