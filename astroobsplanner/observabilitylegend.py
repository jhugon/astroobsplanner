#!/usr/bin/env python2
# vim: set fileencoding=utf-8

import unicodedata
import matplotlib.patches
import matplotlib.lines
import matplotlib.collections
import matplotlib.colors
import matplotlib.cm

class LegendForObservability(object):
  def __init__(self,ax,colorsToShow,labels,obsplot,horizontal=True,showMoon=False,hatchList=None):
    assert(len(colorsToShow)==len(labels))
    sun_patch = matplotlib.patches.Patch(color='y')
    if hatchList:
      assert(len(hatchList)==len(labels))
      sun_patch = matplotlib.patches.Patch(color='0.5')
    self.proxyArtists = [sun_patch]
    self.labels = ["Sun"]

    if showMoon:
        self.labels.append("Moon")
        self.proxyArtists.append(MoonBars())
    
    if hatchList:
      for h in hatchList:
        self.proxyArtists.append(matplotlib.patches.Patch(hatch=h,
                            lw=0,
                            facecolor=matplotlib.colors.colorConverter.to_rgba('k',alpha=0.),
                            edgecolor=matplotlib.colors.colorConverter.to_rgba('k',alpha=1.)
                         ))
    else:
      for c in colorsToShow:
        self.proxyArtists.append(matplotlib.patches.Patch(color=c,alpha=0.5))
    for l in labels:
      lwords = l.split(' ')
      lwordsNew = []
      for word in lwords:
        wordNew = str(word)
        for codePointInt in range(0x03B1,0x3CA): # greek lowercase unicode
          codePointStrUnicode = chr(codePointInt)
          codePointLetterName = unicodedata.name(codePointStrUnicode).split(' ')[-1].lower()
          if word.lower() == codePointLetterName:
            wordNew = codePointStrUnicode
        lwordsNew.append(wordNew)
      l = ' '.join(lwordsNew)
      self.labels.append(l)
      
    ncol = 1
    if horizontal:
      ncol = len(self.proxyArtists)
    self.leg = ax.legend(self.proxyArtists,self.labels,
                            handler_map={MoonBars: MoonBarsHandler()},
                            mode='expand', borderaxespad=0.,
                            ncol=ncol,frameon=False
                        )
    textToPrint = "Regions Show Times When \nAlt > {0}° (Sun Alt > {1}°)".format(obsplot.minAlt,obsplot.minAltSun)
    if horizontal:
      ax.text(0.5,0.5,textToPrint,
                  horizontalalignment="center",verticalalignment="top",
                  transform=ax.transAxes,size='large'
              )
    else:
      ax.text(0.5,0.0,textToPrint,
                  horizontalalignment="center",verticalalignment="top",
                  transform=ax.transAxes,size='large'
              )
    ax.axis('off')



class MoonBars(object):
    pass

class MoonBarsHandler(object):
    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        #x0, y0 = handlebox.xdescent, handlebox.ydescent
        #width, height = handlebox.width, handlebox.height
        #patch = matplotlib.patches.Rectangle([x0, y0], width, height, facecolor='red',
        #                           edgecolor='black', hatch='xx', lw=3,
        #                           transform=handlebox.get_transform())
        #handlebox.add_artist(patch)
        #return patch

        #x0, y0 = handlebox.xdescent, handlebox.ydescent
        #width, height = handlebox.width, handlebox.height
        #y1 = y0+height
        #line = matplotlib.lines.Line2D([x0,x0],[y0,y1])
        #handlebox.add_artist(line)
        #return line


        x0, y0 = handlebox.xdescent, handlebox.ydescent
        width, height = handlebox.width, handlebox.height
        y1 = y0+height
        x1 = x0 +0.2*width
        x2 = x0 +0.4*width
        x3 = x0 +0.6*width
        x4 = x0 +0.8*width
        x5 = x0 +width
        line = matplotlib.collections.LineCollection(
                [
                    [[x0,y0],[x0,y1]],
                    [[x1,y0],[x1,y1]],
                    [[x2,y0],[x2,y1]],
                    [[x3,y0],[x3,y1]],
                    [[x4,y0],[x4,y1]],
                    [[x5,y0],[x5,y1]],
                ], # end line collection
                linewidths=2,
                colors= matplotlib.cm.binary([0.,0.2,0.4,0.6,0.8,1.])
        )
        handlebox.add_artist(line)
        return line

    def __call__(self,*argv,**argk):
        """
        Necessary for matplotlib 1.2.1 to work.
        1.4.1 works with just legend_artist method.
        """
        self.legend_artist(*argv,**argk)
