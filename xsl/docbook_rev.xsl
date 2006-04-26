<?xml version="1.0"?>
<!--
Taken from diffmk by N. Walsh
http://wwws.sun.com/software/xml/developers/diffmk/

TODO: better integration with xmlrev output
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
 
<xsl:import href="docbook.xsl"/>
 
<xsl:template match="*[@revisionflag]">
   <xsl:choose>
     <xsl:when test="local-name(.) = 'para'
                     or local-name(.) = 'section'
                     or local-name(.) = 'appendix'">
       <div CLASS='{@revisionflag}'>
     <xsl:apply-imports/>
       </div>
     </xsl:when>
     <xsl:when test="local-name(.) = 'phrase'
                     or local-name(.) = 'ulink'
                     or local-name(.) = 'xref'">
       <span CLASS='{@revisionflag}'>
     <xsl:apply-imports/>
       </span>
     </xsl:when>
     <xsl:otherwise>
       <xsl:message>
     <xsl:text>Revisionflag on unexpected element: </xsl:text>
     <xsl:value-of select="local-name(.)"/>
     <xsl:text>(Assuming block)</xsl:text>
       </xsl:message>
       <div CLASS='{@revisionflag}'>
     <xsl:apply-imports/>
       </div>
     </xsl:otherwise>
   </xsl:choose>
</xsl:template>
 
</xsl:stylesheet>