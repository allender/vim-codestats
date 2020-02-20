"
" Vim side file to integrate support for codestats.net
"

" check for python 3.  Right now that is what is supported
if !has('python3')
	echomsg 'Python3 support required for vim-codestats'
	finish
endif

" check for variables that are needed and only
" assign them if they are not already assigned
if !exists("g:vim_codestats_url")
	let g:vim_codestats_url = 'https://codestats.net/'
endif

if !exists("g:vim_codestats_key")
	let g:vim_codestats_key = ''
endif

" get the module path there the python file is located
let s:module_path = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" load up the python file
execute 'py3file ' . s:module_path . '/codestats_request.py'

" function to send xp - done on buffer write
function! s:send_xp()
	execute 'python3 codestats.add_xp("' . &filetype . '", ' . b:current_xp ')'
	let b:current_xp = 0
endfunction

" local function to add xp
function! s:add_xp()
	let b:current_xp += 1
endfunction

" local function to exit (which will send any remaining xp)
function! s:exit()
	execute 'python3 codestats.exit()'
endfunction

" set xp to 0 when entering any buffer if
" it's not already set
function! s:enter_buf()
	if !exists("b:current_xp")
		let b:current_xp = 0
	endif
endfunction

function! codestats#set_error(error)
	if a:error == ''
		if exists("g:vim_codestats_error")
			unlet g:vim_codestats_error
		endif
	else
		let g:codestats_error = error
	endif
endfunction

" autocommands to keep track of code stats
augroup codestats
    autocmd!
	autocmd InsertCharPre * call s:add_xp()
    autocmd TextChanged * call s:add_xp()
    autocmd VimLeavePre * call s:exit()
	autocmd BufWrite * call s:send_xp()
	autocmd BufEnter * call s:enter_buf()
augroup END

function! CodeStatsXP()
	if exists("g:vim_codestats_error")
		return "C::S ERR"
	endif
	return 'C::S ' . b:current_xp
endfunction

