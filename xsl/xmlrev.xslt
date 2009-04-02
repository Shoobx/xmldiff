<?xml version="1.0" encoding="ISO-8859-1" ?>

<!--
-
- (c) 2001-2002 Nicolas Chauvat <nico@logilab.fr> - License is GPL
-
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xupdate="http://www.xmldb.org/xupdate"
                exclude-result-prefixes="xsl"
                version="1.0">

<xsl:output method="xml" indent="yes"/>

<!-- generique -->

<xsl:template match="/">
  <xsl:element name="xsl:stylesheet">
    <xsl:attribute name="version">1.0</xsl:attribute>

    <xsl:element name="xsl:output">
      <xsl:attribute name="method">xml</xsl:attribute>
      <xsl:attribute name="indent">yes</xsl:attribute>
    </xsl:element>

    <xsl:element name="xsl:template">
       <xsl:attribute name="match">node()</xsl:attribute>
       <xsl:element name="xsl:copy">
         <xsl:element name="xsl:apply-templates">
           <xsl:attribute name="select">*|@*|text()</xsl:attribute>
         </xsl:element>
       </xsl:element>
    </xsl:element>

    <xsl:element name="xsl:template">
       <xsl:attribute name="match">@*|text()</xsl:attribute>
       <xsl:element name="xsl:copy-of">
         <xsl:attribute name="select">.</xsl:attribute>
       </xsl:element>
    </xsl:element>

    <xsl:apply-templates select="xupdate:modifications/*"/>

  </xsl:element>

</xsl:template>

<!-- XUPDATE:UPDATE -->

<xsl:template match="xupdate:update">
    <xsl:element name="xsl:template">
      <xsl:choose>
        <xsl:when test="contains(@select,'text()')">
          <xsl:attribute name="match"><xsl:value-of select="substring-before(@select,'/text()')"/></xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="match"><xsl:value-of select="@select"/></xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
 
       <xsl:element name="xsl:copy">
         <xsl:element name="xsl:attribute">
           <xsl:attribute name="name">revisionflag</xsl:attribute>
           <xsl:text>changed</xsl:text>
         </xsl:element>

         <xsl:element name="xsl:apply-templates"/>

       </xsl:element>

    </xsl:element>
</xsl:template>

<!-- XUPDATE:REMOVE -->

<xsl:template match="xupdate:remove">
    <xsl:element name="xsl:template">
      <xsl:attribute name="match"><xsl:value-of select="@select"/></xsl:attribute>
       <xsl:element name="xsl:copy">
         <xsl:element name="xsl:attribute">
           <xsl:attribute name="name">revisionflag</xsl:attribute>
           <xsl:text>removed</xsl:text>
         </xsl:element>
       </xsl:element>

       <xsl:element name="xsl:apply-templates"/>

    </xsl:element>
</xsl:template>

<!-- XUPDATE:INSERT-BEFORE -->

  <xsl:template match="xupdate:insert-before">
    <!-- FIXME/TODO -->
    <xsl:message>FIXME/TODO: xupdate:insert-before is not implemented yet. Care to help ?</xsl:message>
  </xsl:template>

<!-- XUPDATE:INSERT-AFTER -->

  <xsl:template match="xupdate:insert-after">
    <!-- FIXME/TODO -->
    <xsl:message>FIXME/TODO: xupdate:insert-after is not implemented yet. Care to help ?</xsl:message>
  </xsl:template>

<!-- XUPDATE:RENAME -->

  <xsl:template match="xupdate:rename">
    <xsl:element name="xsl:template">
      <xsl:attribute name="match"><xsl:value-of select="@select"/></xsl:attribute>
      <xsl:element name="xsl:element">
	<xsl:attribute name="name"><xsl:value-of select="text()"/></xsl:attribute>
	<xsl:element name="xsl:attribute">
	  <xsl:attribute name="name">revisionflag</xsl:attribute>
	  <xsl:text>removed</xsl:text>
	</xsl:element>
	<xsl:element name="xsl:copy-of">
	  <xsl:attribute name="select"><xsl:text>@*|*|text()</xsl:text></xsl:attribute>
	</xsl:element>
      </xsl:element>

      <xsl:element name="xsl:apply-templates"/>

    </xsl:element>
  </xsl:template>

<!-- XUPDATE:APPEND -->

  <xsl:template match="xupdate:append">
    <!-- FIXME/TODO -->
    <xsl:message>FIXME/TODO: xupdate:append is not implemented yet. Care to help ?</xsl:message>
  </xsl:template>

</xsl:stylesheet>
