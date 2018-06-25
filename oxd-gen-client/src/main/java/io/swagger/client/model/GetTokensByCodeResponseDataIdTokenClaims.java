package io.swagger.client.model;

import java.util.Objects;
import com.google.gson.TypeAdapter;
import com.google.gson.annotations.JsonAdapter;
import com.google.gson.annotations.SerializedName;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * GetTokensByCodeResponseDataIdTokenClaims
 */
@javax.annotation.Generated(value = "io.swagger.codegen.languages.JavaClientCodegen", date = "2018-06-25T15:27:32.160Z")
public class GetTokensByCodeResponseDataIdTokenClaims {
  @SerializedName("at_hash")
  private List<String> atHash = new ArrayList<String>();

  @SerializedName("aud")
  private List<String> aud = new ArrayList<String>();

  @SerializedName("sub")
  private List<String> sub = new ArrayList<String>();

  @SerializedName("auth_time")
  private List<String> authTime = new ArrayList<String>();

  @SerializedName("iss")
  private List<String> iss = new ArrayList<String>();

  @SerializedName("exp")
  private List<String> exp = new ArrayList<String>();

  @SerializedName("iat")
  private List<String> iat = new ArrayList<String>();

  @SerializedName("nonce")
  private List<String> nonce = new ArrayList<String>();

  @SerializedName("oxOpenIDConnectVersion")
  private List<String> oxOpenIDConnectVersion = new ArrayList<String>();

  public GetTokensByCodeResponseDataIdTokenClaims atHash(List<String> atHash) {
    this.atHash = atHash;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addAtHashItem(String atHashItem) {
    this.atHash.add(atHashItem);
    return this;
  }

   /**
   * Get atHash
   * @return atHash
  **/
  @ApiModelProperty(example = "[\"Cx2dz5Wvw_kBXAcTs3mFA\"]", required = true, value = "")
  public List<String> getAtHash() {
    return atHash;
  }

  public void setAtHash(List<String> atHash) {
    this.atHash = atHash;
  }

  public GetTokensByCodeResponseDataIdTokenClaims aud(List<String> aud) {
    this.aud = aud;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addAudItem(String audItem) {
    this.aud.add(audItem);
    return this;
  }

   /**
   * Get aud
   * @return aud
  **/
  @ApiModelProperty(example = "[\"l238j323ds-23ij4\"]", required = true, value = "")
  public List<String> getAud() {
    return aud;
  }

  public void setAud(List<String> aud) {
    this.aud = aud;
  }

  public GetTokensByCodeResponseDataIdTokenClaims sub(List<String> sub) {
    this.sub = sub;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addSubItem(String subItem) {
    this.sub.add(subItem);
    return this;
  }

   /**
   * Get sub
   * @return sub
  **/
  @ApiModelProperty(example = "[\"jblack\"]", required = true, value = "")
  public List<String> getSub() {
    return sub;
  }

  public void setSub(List<String> sub) {
    this.sub = sub;
  }

  public GetTokensByCodeResponseDataIdTokenClaims authTime(List<String> authTime) {
    this.authTime = authTime;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addAuthTimeItem(String authTimeItem) {
    this.authTime.add(authTimeItem);
    return this;
  }

   /**
   * Get authTime
   * @return authTime
  **/
  @ApiModelProperty(required = true, value = "")
  public List<String> getAuthTime() {
    return authTime;
  }

  public void setAuthTime(List<String> authTime) {
    this.authTime = authTime;
  }

  public GetTokensByCodeResponseDataIdTokenClaims iss(List<String> iss) {
    this.iss = iss;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addIssItem(String issItem) {
    this.iss.add(issItem);
    return this;
  }

   /**
   * Get iss
   * @return iss
  **/
  @ApiModelProperty(example = "[\"https://as.gluu.org/\"]", required = true, value = "")
  public List<String> getIss() {
    return iss;
  }

  public void setIss(List<String> iss) {
    this.iss = iss;
  }

  public GetTokensByCodeResponseDataIdTokenClaims exp(List<String> exp) {
    this.exp = exp;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addExpItem(String expItem) {
    this.exp.add(expItem);
    return this;
  }

   /**
   * Get exp
   * @return exp
  **/
  @ApiModelProperty(required = true, value = "")
  public List<String> getExp() {
    return exp;
  }

  public void setExp(List<String> exp) {
    this.exp = exp;
  }

  public GetTokensByCodeResponseDataIdTokenClaims iat(List<String> iat) {
    this.iat = iat;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addIatItem(String iatItem) {
    this.iat.add(iatItem);
    return this;
  }

   /**
   * Get iat
   * @return iat
  **/
  @ApiModelProperty(required = true, value = "")
  public List<String> getIat() {
    return iat;
  }

  public void setIat(List<String> iat) {
    this.iat = iat;
  }

  public GetTokensByCodeResponseDataIdTokenClaims nonce(List<String> nonce) {
    this.nonce = nonce;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addNonceItem(String nonceItem) {
    this.nonce.add(nonceItem);
    return this;
  }

   /**
   * Get nonce
   * @return nonce
  **/
  @ApiModelProperty(required = true, value = "")
  public List<String> getNonce() {
    return nonce;
  }

  public void setNonce(List<String> nonce) {
    this.nonce = nonce;
  }

  public GetTokensByCodeResponseDataIdTokenClaims oxOpenIDConnectVersion(List<String> oxOpenIDConnectVersion) {
    this.oxOpenIDConnectVersion = oxOpenIDConnectVersion;
    return this;
  }

  public GetTokensByCodeResponseDataIdTokenClaims addOxOpenIDConnectVersionItem(String oxOpenIDConnectVersionItem) {
    this.oxOpenIDConnectVersion.add(oxOpenIDConnectVersionItem);
    return this;
  }

   /**
   * Get oxOpenIDConnectVersion
   * @return oxOpenIDConnectVersion
  **/
  @ApiModelProperty(required = true, value = "")
  public List<String> getOxOpenIDConnectVersion() {
    return oxOpenIDConnectVersion;
  }

  public void setOxOpenIDConnectVersion(List<String> oxOpenIDConnectVersion) {
    this.oxOpenIDConnectVersion = oxOpenIDConnectVersion;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    GetTokensByCodeResponseDataIdTokenClaims getTokensByCodeResponseDataIdTokenClaims = (GetTokensByCodeResponseDataIdTokenClaims) o;
    return Objects.equals(this.atHash, getTokensByCodeResponseDataIdTokenClaims.atHash) &&
        Objects.equals(this.aud, getTokensByCodeResponseDataIdTokenClaims.aud) &&
        Objects.equals(this.sub, getTokensByCodeResponseDataIdTokenClaims.sub) &&
        Objects.equals(this.authTime, getTokensByCodeResponseDataIdTokenClaims.authTime) &&
        Objects.equals(this.iss, getTokensByCodeResponseDataIdTokenClaims.iss) &&
        Objects.equals(this.exp, getTokensByCodeResponseDataIdTokenClaims.exp) &&
        Objects.equals(this.iat, getTokensByCodeResponseDataIdTokenClaims.iat) &&
        Objects.equals(this.nonce, getTokensByCodeResponseDataIdTokenClaims.nonce) &&
        Objects.equals(this.oxOpenIDConnectVersion, getTokensByCodeResponseDataIdTokenClaims.oxOpenIDConnectVersion);
  }

  @Override
  public int hashCode() {
    return Objects.hash(atHash, aud, sub, authTime, iss, exp, iat, nonce, oxOpenIDConnectVersion);
  }


  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class GetTokensByCodeResponseDataIdTokenClaims {\n");
    
    sb.append("    atHash: ").append(toIndentedString(atHash)).append("\n");
    sb.append("    aud: ").append(toIndentedString(aud)).append("\n");
    sb.append("    sub: ").append(toIndentedString(sub)).append("\n");
    sb.append("    authTime: ").append(toIndentedString(authTime)).append("\n");
    sb.append("    iss: ").append(toIndentedString(iss)).append("\n");
    sb.append("    exp: ").append(toIndentedString(exp)).append("\n");
    sb.append("    iat: ").append(toIndentedString(iat)).append("\n");
    sb.append("    nonce: ").append(toIndentedString(nonce)).append("\n");
    sb.append("    oxOpenIDConnectVersion: ").append(toIndentedString(oxOpenIDConnectVersion)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(java.lang.Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }

}

