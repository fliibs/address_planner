debImport "-ssf" "novas.fsdb"
debLoadSimResult /home/liuyunqi/huangtao/ap/dv/novas.fsdb
wvCreateWindow
verdiDockWidgetDisplay -dock widgetDock_WelcomePage
verdiDockWidgetHide -dock widgetDock_WelcomePage
verdiWindowResize -win $_Verdi_1 -32 -12 "1908" "1007"
srcHBSelect "tb_top.u_dut" -win $_nTrace1
srcSetScope -win $_nTrace1 "tb_top.u_dut" -delim "."
srcSelect -signal "clk" -win $_nTrace1
srcSelect -signal "rst_n" -win $_nTrace1
srcSelect -signal "p_addr" -win $_nTrace1
srcSelect -signal "p_prot" -win $_nTrace1
srcSelect -signal "p_sel" -win $_nTrace1
srcSelect -signal "p_enable" -win $_nTrace1
srcSelect -signal "p_write" -win $_nTrace1
srcSelect -signal "p_wdata" -win $_nTrace1
srcSelect -signal "p_strb" -win $_nTrace1
srcSelect -signal "p_ready" -win $_nTrace1
srcSelect -signal "p_rdata" -win $_nTrace1
srcSelect -signal "p_slverr" -win $_nTrace1
srcAddSelectedToWave -win $_nTrace1
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvZoomOut -win $_nWave2
wvScrollDown -win $_nWave2 1
wvScrollDown -win $_nWave2 1
wvScrollDown -win $_nWave2 0
wvScrollDown -win $_nWave2 0
wvScrollDown -win $_nWave2 0
wvScrollDown -win $_nWave2 0
