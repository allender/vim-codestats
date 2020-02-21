"
" Vim side file to integrate support for codestats.net
"

" define external function to do nothign
" in case module doesn't initialize properly
function! CodeStatsXP()
	return 'C::S Not Initialized'
endfunction

" get the module path where the python file is located
let s:codestats_path = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" check for python 3.  Right now that is what is supported
if !has('python3')
	if !has('python')
		echomsg 'Python2/3 support required for vim-codestats'
		finish
	endif
	let s:python = 'python'

	" load up the python file
	execute 'pyfile ' . s:codestats_path . '/codestats.py'
else
	let s:python = 'python3'
	" load up the python file
	execute 'py3file ' . s:codestats_path . '/codestats.py'
endif

" check for variables that are needed and only
" assign them if they are not already assigned
if !exists("g:codestats_api_url")
	let g:codestats_api_url = 'https://codestats.net/'
endif

if !exists("g:codestats_api_key")
	let g:codestats_api_key = ''
endif

" function to send xp - done on buffer write
function! s:send_xp()
	execute s:python . ' codestats.add_xp("' . &filetype . '", ' . b:current_xp ')'
	let b:current_xp = 0
endfunction

" local function to add xp
function! s:add_xp()
	let b:current_xp += 1
endfunction

" local function to exit (which will send any remaining xp)
function! s:exit()
	execute s:python . ' codestats.exit()'
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
