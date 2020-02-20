# VIM CodeStats

A vim plugin for [CodeStats](http://codestats.net)

This plugin requires Python 3.  It also requires the [requests](https://requests.readthedocs.io/en/master/) library.  It makes use of the InsertCharPre autocommand in order to track keystrokes.  It uses threading (and not multiprocessing) so that it should work across all platforms (including windows).

You should be able to use your typical vim plugin manager in order to install.  I use [Pathogen](https://github.com/tpope/vim-pathogen) although I'm sure other managers should work just fine.

## Variables:
* g:vim_codestats_key - machine key as defined on CodeStats
* g:vim_codestats_url - url for CodeStats server.  Defaults to https://codestats.net.  You can set this to a personal or private code stats instance if you wish.  Or you can point it to the https://beta.codestats.net if you are working on your own plugin

## Details
The vim_codestats plugin uses Python 3 in order to manage threads needed to send XP to the codestat server.  On startup, a thread is started at a fixed interval at which any xp that has been recorded will be sent to the CodeState servers.  There is a filetype map at the top of the python file that will translate Vim filetype to a langauge name that is used to display on the page.  CodeStats allows any kind of langauge name to be used so my choices here are somewhat arbitrary although (aside from C/C++) should make sense.  Filetypes and langauges can be added to this mapping as necessary
