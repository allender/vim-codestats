"
" Vim side file to integrate support for codestats.net
"

" check for python 3.  Right now that is
" what is supported
if !has('python3')
	echomsg 'Python3 support required for vim-codestats'
	finish
endif

" currently we also require timers
if !has('timers')
	echomsg 'timers support required for vim-codestats'
	finish
endif

" 
let g:vim_codestats_url = 'https://codestats.net/'
let g:vim_codestats_username = ''
let g:vim_codestats_key = ''

" get the module path there the python file is located
let s:module_path = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" load up the python file
execute 'py3file ' . s:module_path . '/codestats_request.py'
execute 'python3 start_cs_thread()'

" function to send xp - done on buffer write
function! s:codestats_send_xp()
	if exists('b:current_xp')
		execute 'python3 add_xp("' . &filetype . '", ' . b:current_xp ')'
		let b:current_xp = 0
	endif
endfunction

" local function to add xp
function! s:codestats_add_xp()
	if exists('b:current_xp')
		let b:current_xp += 1
	else
		let b:current_xp = 1
	endif
endfunction

" local function to exit (which will send any remaining xp)
function! s:codestats_exit()
	execute 'python3 exit_cs_thread()'
endfunction

" autocommands to keep track of code stats
augroup codestats
    autocmd!
	autocmd InsertCharPre * call s:codestats_add_xp()
    autocmd TextChanged * call s:codestats_add_xp()
    autocmd VimLeavePre * call s:codestats_exit()
	autocmd BufWrite * call s:codestats_send_xp()
augroup END

function! CheckXP()
	" execute the get stats function
	execute 'python3 get_stats()'
endfunction

