// API基础URL
const API_BASE = '/api';

// 全局状态
let currentPage = 'dashboard';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboard();
    setupEventListeners();
    initCompetitionFilters();
    // 初始化所有表格列宽拉伸（thead 静态存在即可初始化）
    initColumnResizer('timePlanTable');
    initColumnResizer('recentDataTable');
    initColumnResizer('competitionsTable');
    initColumnResizer('competitionStudentsTable');
    initColumnResizer('studentsTable');
    // 恢复之前保存的列宽
    ['timePlanTable','recentDataTable','competitionsTable','competitionStudentsTable','studentsTable']
        .forEach(restoreColumnWidths);
});

// 初始化导航
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // 外部链接（如Mermaid图表）直接放行
            if (item.getAttribute('target') === '_blank') return;
            e.preventDefault();
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

// 切换页面
function switchPage(page) {
    currentPage = page;
    
    // 更新导航激活状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
    
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.add('hidden');
    });
    
    // 显示目标页面
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
        targetPage.classList.remove('hidden');
    }
    
    // 更新页面标题
    const titles = {
        'dashboard': '仪表盘',
        'competitions': '竞赛管理',
        'students': '学生管理',
        'data': '数据采集',
        'logs': '系统日志'
    };
    document.getElementById('pageTitle').textContent = titles[page] || '仪表盘';
    
    // 加载页面数据
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'competitions':
            document.getElementById('competitionListView').classList.remove('hidden');
            document.getElementById('competitionDetailView').classList.add('hidden');
            loadCompetitions();
            break;
        case 'students':
            loadStudents();
            break;
        case 'data':
            loadCollectedData();
            break;
        case 'logs':
            loadLogs();
            break;
    }
}

// 设置事件监听器
function setupEventListeners() {
    document.getElementById('addCompetitionBtn')?.addEventListener('click', () => {
        showCompetitionModal();
    });
    
    document.getElementById('addStudentBtn')?.addEventListener('click', () => {
        showStudentModal();
    });
    
    document.getElementById('collectBtn')?.addEventListener('click', triggerCollection);
    document.getElementById('collectDataBtn')?.addEventListener('click', triggerCollection);
    document.getElementById('refreshTimePlanBtn')?.addEventListener('click', refreshTimePlan);
    
    document.getElementById('modalClose')?.addEventListener('click', closeModal);
    document.getElementById('modalCancel')?.addEventListener('click', closeModal);
    
    document.getElementById('backToCompetitionListBtn')?.addEventListener('click', backToCompetitionList);
    
    document.getElementById('addStudentToCompetitionBtn')?.addEventListener('click', () => {
        if (currentCompetitionId) {
            showStudentCompetitionModal(null, currentCompetitionId);
        }
    });
}

// 加载仪表盘数据
async function loadDashboard() {
    try {
        // 加载统计数据
        const statsResponse = await fetch(`${API_BASE}/statistics`);
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            document.getElementById('statCompetitions').textContent = statsData.data.competitions;
            document.getElementById('statStudents').textContent = statsData.data.students;
            document.getElementById('statData').textContent = statsData.data.collected_data;
            document.getElementById('statRelations').textContent = statsData.data.relations;
        }
        
        // 加载最新采集数据
        const dataResponse = await fetch(`${API_BASE}/collected-data`);
        const dataResult = await dataResponse.json();
        
        if (dataResult.success) {
            const tbody = document.querySelector('#recentDataTable tbody');
            tbody.innerHTML = '';
            
            const recentData = dataResult.data.slice(0, 10);
            if (recentData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="empty-state">暂无数据</td></tr>';
            } else {
                recentData.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${escapeHtml(item.title)}</td>
                        <td>${escapeHtml(item.summary || '暂无摘要')}</td>
                        <td>${formatDate(item.collected_at)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        }
        
        // 加载赛程规划
        loadTimePlan();
    } catch (error) {
        showToast('加载仪表盘数据失败', 'error');
        console.error('加载仪表盘数据失败:', error);
    }
}

// 加载赛程规划
async function loadTimePlan() {
    try {
        const response = await fetch(`${API_BASE}/time-plan`);
        const result = await response.json();

        if (result.success) {
            const metaEl = document.getElementById('timePlanMeta');
            if (result.updated_at) {
                metaEl.textContent = `更新于 ${formatDate(result.updated_at)}`;
            } else {
                metaEl.textContent = '尚未更新，点击"更新"按钮从官网获取';
            }

            const tbody = document.querySelector('#timePlanTable tbody');
            tbody.innerHTML = '';

            if (!result.data || result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无赛程数据，点击右上角"更新"按钮从官网获取</td></tr>';
                return;
            }

            result.data.forEach(item => {
                const row = document.createElement('tr');
                const remarkValue = item.remark || '';
                row.innerHTML = `
                    <td>${escapeHtml(item.seq)}</td>
                    <td>${escapeHtml(item.name)}</td>
                    <td>${escapeHtml(item.register_time || '待定')}</td>
                    <td>${escapeHtml(item.submit_time || '待定')}</td>
                    <td>${escapeHtml(item.final_time || '待定')}</td>
                    <td class="remark-cell">
                        <input class="remark-input" type="text" value="${escapeHtml(remarkValue)}" placeholder="添加个人备注..." data-seq="${escapeHtml(item.seq)}">
                        <button class="remark-save-btn" data-seq="${escapeHtml(item.seq)}" title="保存备注">✓</button>
                    </td>
                `;
                tbody.appendChild(row);
            });

            document.querySelectorAll('.remark-save-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const seq = this.getAttribute('data-seq');
                    const input = document.querySelector(`.remark-input[data-seq="${seq}"]`);
                    saveRemark(seq, input.value);
                });
            });

            document.querySelectorAll('.remark-input').forEach(input => {
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        const seq = this.getAttribute('data-seq');
                        saveRemark(seq, this.value);
                    }
                });
            });
        }
    } catch (error) {
        console.error('加载赛程规划失败:', error);
    }
}

// 保存个人备注
async function saveRemark(seq, remark) {
    const btn = document.querySelector(`.remark-save-btn[data-seq="${seq}"]`);
    if (btn) {
        btn.textContent = '...';
        btn.disabled = true;
    }

    try {
        const response = await fetch(`${API_BASE}/time-plan/remark`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seq, remark })
        });
        const result = await response.json();

        if (result.success) {
            const input = document.querySelector(`.remark-input[data-seq="${seq}"]`);
            if (input) {
                input.style.borderColor = 'var(--emerald)';
                setTimeout(() => { input.style.borderColor = ''; }, 1500);
            }
            if (btn) {
                btn.textContent = '✓';
            }
        } else {
            showToast(`保存备注失败: ${result.message}`, 'error');
            if (btn) btn.textContent = '✗';
        }
    } catch (error) {
        showToast('保存备注失败', 'error');
        console.error('保存备注失败:', error);
        if (btn) btn.textContent = '✗';
    } finally {
        if (btn) {
            btn.disabled = false;
            setTimeout(() => {
                if (btn) btn.textContent = '✓';
            }, 1000);
        }
    }
}

// 刷新赛程规划
async function refreshTimePlan() {
    const btn = document.getElementById('refreshTimePlanBtn');
    btn.disabled = true;
    btn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite">&#x21bb;</span> 更新中...';

    try {
        const response = await fetch(`${API_BASE}/time-plan/refresh`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showToast(result.message || '赛程规划刷新成功', 'success');
            loadTimePlan();
        } else {
            showToast(`刷新失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast('刷新赛程规划失败', 'error');
        console.error('刷新赛程规划失败:', error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            更新`;
    }
}

// ============================================
//   列宽自由拉伸
// ============================================
function initColumnResizer(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const headers = table.querySelectorAll('th');
    headers.forEach(th => {
        if (th.querySelector('.resize-handle')) return;
        const handle = document.createElement('div');
        handle.className = 'resize-handle';
        th.appendChild(handle);

        let startX, startWidth;
        const onMouseMove = (e) => {
            const diff = e.clientX - startX;
            const newWidth = Math.max(40, startWidth + diff);
            th.style.width = newWidth + 'px';
            th.style.minWidth = newWidth + 'px';
        };
        const onMouseUp = () => {
            table.classList.remove('resizing');
            handle.classList.remove('resizing');
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            saveColumnWidths(tableId);
        };
        handle.addEventListener('mousedown', (e) => {
            startX = e.clientX;
            startWidth = th.offsetWidth;
            table.classList.add('resizing');
            handle.classList.add('resizing');
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
        });
    });
}

function saveColumnWidths(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const widths = [];
    table.querySelectorAll('th').forEach(th => {
        widths.push(th.style.width || '');
    });
    localStorage.setItem('col_widths_' + tableId, JSON.stringify(widths));
}

function restoreColumnWidths(tableId) {
    const saved = localStorage.getItem('col_widths_' + tableId);
    if (!saved) return;
    const widths = JSON.parse(saved);
    const table = document.getElementById(tableId);
    if (!table) return;
    table.querySelectorAll('th').forEach((th, i) => {
        if (widths[i]) {
            th.style.width = widths[i];
            th.style.minWidth = widths[i];
        }
    });
}

// 当前查看的竞赛ID
let currentCompetitionId = null;

// 竞赛状态筛选
let competitionStatusFilter = ['active', 'upcoming', 'completed'];

function initCompetitionFilters() {
    const filterBar = document.getElementById('competitionFilterBar');
    if (!filterBar) return;
    const checkboxes = filterBar.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            competitionStatusFilter = Array.from(checkboxes)
                .filter(c => c.checked)
                .map(c => c.value);
            loadCompetitions();
        });
    });
}

// 加载竞赛列表
async function loadCompetitions() {
    try {
        const response = await fetch(`${API_BASE}/competitions`);
        const result = await response.json();

        if (result.success) {
            const tbody = document.querySelector('#competitionsTable tbody');
            tbody.innerHTML = '';

            const filteredData = result.data.filter(comp => competitionStatusFilter.includes(comp.status));

            if (filteredData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:48px 0;color:var(--storm-cloud)">暂无符合条件的竞赛数据</td></tr>';
            } else {
                for (const comp of filteredData) {
                    const row = document.createElement('tr');

                    const safeName = escapeHtml(comp.name);
                    const safeUrl = escapeUrl(comp.official_url);
                    const safeDisplayText = escapeHtml(comp.official_url || '无');
                    const safeDate = comp.end_date ? formatDate(comp.end_date) : '未设置';
                    const safeCategory = escapeHtml(comp.category || '未分类');
                    const statusClass = comp.status === 'active' ? 'active' : comp.status === 'upcoming' ? 'pending' : 'ended';
                    const statusText = getStatusText(comp.status);

                    let studentCount = 0;
                    try {
                        const studentsResponse = await fetch(`${API_BASE}/student-competitions?competition_id=${comp.id}`);
                        const studentsResult = await studentsResponse.json();
                        studentCount = studentsResult.success ? studentsResult.data.length : 0;
                    } catch(e) {}

                    const td1 = document.createElement('td');
                    td1.textContent = comp.name;
                    row.appendChild(td1);

                    const td2 = document.createElement('td');
                    if (comp.official_url && /^https?:\/\//i.test(comp.official_url)) {
                        const a = document.createElement('a');
                        a.href = comp.official_url;
                        a.target = '_blank';
                        a.rel = 'noopener noreferrer';
                        a.className = 'truncate';
                        a.textContent = comp.official_url;
                        td2.appendChild(a);
                    } else {
                        td2.textContent = '无';
                        td2.className = 'text-muted';
                    }
                    row.appendChild(td2);

                    const td3 = document.createElement('td');
                    td3.textContent = safeDate;
                    row.appendChild(td3);

                    const td4 = document.createElement('td');
                    td4.textContent = comp.category || '未分类';
                    row.appendChild(td4);

                    const td5 = document.createElement('td');
                    const badge = document.createElement('span');
                    badge.className = `badge badge-${statusClass}`;
                    badge.textContent = statusText;
                    td5.appendChild(badge);
                    row.appendChild(td5);

                    const td6 = document.createElement('td');
                    td6.className = 'text-mono';
                    td6.textContent = studentCount;
                    row.appendChild(td6);

                    const td7 = document.createElement('td');
                    td7.innerHTML = `<button class="btn btn-sm btn-ghost" onclick="viewCompetitionDetail(${comp.id})">查看详情</button><button class="btn btn-sm btn-ghost" onclick="editCompetition(${comp.id})">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteCompetition(${comp.id})">删除</button>`;
                    row.appendChild(td7);

                    tbody.appendChild(row);
                }
            }
        }
    } catch (error) {
        showToast('加载竞赛列表失败', 'error');
        console.error('加载竞赛列表失败:', error);
    }
}

// 查看竞赛详情
async function viewCompetitionDetail(competitionId) {
    currentCompetitionId = competitionId;
    
    document.getElementById('competitionListView').classList.add('hidden');
    document.getElementById('competitionDetailView').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/competitions/${competitionId}/students`);
        const result = await response.json();
        
        if (result.success) {
            const competition = result.data.competition;
            document.getElementById('competitionDetailName').textContent = competition.name;
            
            const urlEl = document.getElementById('competitionDetailUrl');
            urlEl.textContent = competition.official_url || '无';
            urlEl.href = (competition.official_url && /^https?:\/\//i.test(competition.official_url)) ? competition.official_url : '#';
            urlEl.rel = 'noopener noreferrer';
            
            document.getElementById('competitionDetailEndDate').textContent = competition.end_date ? formatDate(competition.end_date) : '未设置';
            document.getElementById('competitionDetailCategory').textContent = competition.category || '未分类';

            initFileBrowser(competitionId);

            const statusEl = document.getElementById('competitionDetailStatus');
            statusEl.innerHTML = '';
            const statusBadge = document.createElement('span');
            statusBadge.className = `badge badge-${competition.status === 'active' ? 'active' : competition.status === 'upcoming' ? 'pending' : 'ended'}`;
            statusBadge.textContent = getStatusText(competition.status);
            statusEl.appendChild(statusBadge);
            
            const materialsEl = document.getElementById('competitionDetailMaterials');
            materialsEl.innerHTML = '';

            const officialFiles = competition.official_materials_files || [];
            const dbMaterials = competition.official_materials ? (() => { try { return JSON.parse(competition.official_materials); } catch(e) { return []; } })() : [];

            const hasMaterials = officialFiles.length > 0 || dbMaterials.length > 0;

            if (hasMaterials) {
                const wrapper = document.createElement('div');
                wrapper.className = 'materials-wrapper';

                const header = document.createElement('div');
                header.className = 'materials-header';

                const countBadge = document.createElement('span');
                countBadge.className = 'materials-count';
                countBadge.textContent = `共 ${officialFiles.length + dbMaterials.length} 个文件`;
                header.appendChild(countBadge);

                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'btn btn-sm btn-ghost materials-toggle-btn';
                toggleBtn.textContent = '收起';
                toggleBtn.dataset.collapsed = 'false';
                toggleBtn.onclick = () => {
                    const isCollapsed = toggleBtn.dataset.collapsed === 'true';
                    toggleBtn.dataset.collapsed = isCollapsed ? 'false' : 'true';
                    toggleBtn.textContent = isCollapsed ? '收起' : '展开';
                    listContainer.classList.toggle('collapsed', !isCollapsed);
                };
                header.appendChild(toggleBtn);
                wrapper.appendChild(header);

                const listContainer = document.createElement('div');
                listContainer.className = 'material-links';
                listContainer.id = 'officialMaterialsList';

                // 自动扫描的官方材料文件
                officialFiles.forEach(f => {
                    const a = document.createElement('a');
                    a.href = `${API_BASE}/files/serve/${competitionId}?path=${encodeURIComponent(f.path)}`;
                    a.target = '_blank';
                    a.className = 'material-link';
                    a.title = f.name + ' (' + formatFileSize(f.size) + ')';
                    a.innerHTML = `<span class="material-link-icon">${getFileIcon(f.name)}</span><span class="material-link-name">${escapeHtml(f.name)}</span><span class="material-link-size">${formatFileSize(f.size)}</span>`;
                    listContainer.appendChild(a);
                });

                // 数据库中存储的官方材料链接
                dbMaterials.forEach(m => {
                    const a = document.createElement('a');
                    a.href = escapeUrl(m.url || '');
                    a.target = '_blank';
                    a.rel = 'noopener noreferrer';
                    a.textContent = m.name;
                    a.className = 'material-link';
                    listContainer.appendChild(a);
                });

                wrapper.appendChild(listContainer);
                materialsEl.appendChild(wrapper);
            } else {
                materialsEl.textContent = '暂无';
            }
            
            const tbody = document.querySelector('#competitionStudentsTable tbody');
            tbody.innerHTML = '';
            
            const students = result.data.students;
            if (students.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:48px 0;color:var(--storm-cloud)">暂无参赛学生，点击"添加参赛学生"开始</td></tr>';
            } else {
                students.forEach(student => {
                    const row = document.createElement('tr');
                    
                    const td1 = document.createElement('td');
                    td1.textContent = student.student_name;
                    row.appendChild(td1);
                    
                    const tdAccount = document.createElement('td');
                    tdAccount.className = 'text-mono';
                    tdAccount.textContent = student.account || student.phone || '未填写';
                    row.appendChild(tdAccount);
                    
                    const td2 = document.createElement('td');
                    const displayGrade = student.folder_grade || student.grade || '';
                    const displayMajor = student.major || '';
                    td2.textContent = displayGrade + (displayGrade && displayMajor ? '/' : '') + displayMajor;
                    row.appendChild(td2);
                    
                    const td3 = document.createElement('td');
                    td3.textContent = student.folder_project_name || student.project_name || '未设置';
                    row.appendChild(td3);
                    
                    const td4 = document.createElement('td');
                    td4.textContent = student.role || '未设置';
                    row.appendChild(td4);
                    
                    const td5 = document.createElement('td');
                    const sBadge = document.createElement('span');
                    sBadge.className = `badge badge-${getRegistrationStatusClass(student.registration_status)}`;
                    sBadge.textContent = getRegistrationStatusText(student.registration_status);
                    td5.appendChild(sBadge);
                    row.appendChild(td5);
                    
                    const td6 = document.createElement('td');
                    const materialWrapper = document.createElement('div');
                    materialWrapper.className = 'student-materials-cell';

                    // 数据库中上传的材料
                    if (student.material_files) {
                        try {
                            const materials = JSON.parse(student.material_files);
                            if (materials.length > 0) {
                                const dbList = document.createElement('div');
                                dbList.className = 'material-list';
                                materials.forEach(f => {
                                    const a = document.createElement('a');
                                    a.href = `/api/download-material/${escapeHtml(f)}`;
                                    a.className = 'material-file';
                                    a.download = '';
                                    a.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' + escapeHtml(f);
                                    dbList.appendChild(a);
                                });
                                materialWrapper.appendChild(dbList);
                            }
                        } catch(e) {}
                    }

                    // 自动映射的参赛学生文件夹中的报名材料
                    const regMaterials = student.folder_registration_materials || [];
                    if (regMaterials.length > 0) {
                        const regSection = document.createElement('div');
                        regSection.className = 'material-section';
                        const regTitle = document.createElement('div');
                        regTitle.className = 'material-section-title';
                        regTitle.textContent = '报名材料';
                        regSection.appendChild(regTitle);
                        const regList = document.createElement('div');
                        regList.className = 'material-list';
                        regMaterials.forEach(f => {
                            const a = document.createElement('a');
                            a.href = `/${escapeHtml(f.path)}`;
                            a.className = 'material-file';
                            a.download = '';
                            a.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' + escapeHtml(f.name);
                            regList.appendChild(a);
                        });
                        regSection.appendChild(regList);
                        materialWrapper.appendChild(regSection);
                    }

                    // 自动映射的参赛学生文件夹
                    const matchedFolders = student.matched_folders || [];
                    if (matchedFolders.length > 0) {
                        const folderList = document.createElement('div');
                        folderList.className = 'student-folder-list';
                        matchedFolders.forEach(folder => {
                            const folderChip = document.createElement('a');
                            folderChip.className = 'student-folder-chip';
                            folderChip.href = '#';
                            folderChip.title = folder.name;
                            folderChip.innerHTML = `<span class="folder-icon">📁</span><span class="folder-name">${escapeHtml(folder.name)}</span>`;
                            folderChip.onclick = (e) => {
                                e.preventDefault();
                                // 打开文件浏览器并定位到该学生文件夹
                                document.getElementById('fileBrowserPanel').scrollIntoView({ behavior: 'smooth' });
                                browseCompetitionFiles(folder.path);
                                // 同步侧边栏高亮
                                document.querySelectorAll('#fileBrowserSidebar .sidebar-quick-link').forEach(l => l.classList.remove('active'));
                            };
                            folderList.appendChild(folderChip);
                        });
                        materialWrapper.appendChild(folderList);
                    }

                    if (materialWrapper.childNodes.length === 0) {
                        td6.textContent = '无';
                    } else {
                        td6.appendChild(materialWrapper);
                    }
                    row.appendChild(td6);
                    
                    const td7 = document.createElement('td');
                    td7.innerHTML = `<button class="btn btn-sm btn-ghost" onclick="editStudentCompetition(${student.relation_id})">编辑</button><button class="btn btn-sm btn-ghost" onclick="uploadMaterial(${student.relation_id})">上传材料</button><button class="btn btn-sm btn-danger" onclick="deleteStudentCompetition(${student.relation_id})">删除</button>`;
                    row.appendChild(td7);
                    
                    tbody.appendChild(row);
                });
            }
        }
    } catch (error) {
        showToast('加载竞赛详情失败', 'error');
        console.error('加载竞赛详情失败:', error);
    }
}

// 返回竞赛列表
function backToCompetitionList() {
    currentCompetitionId = null;
    document.getElementById('competitionDetailView').classList.add('hidden');
    document.getElementById('competitionListView').classList.remove('hidden');
    loadCompetitions();
}

// 获取参赛状态样式类
function getRegistrationStatusClass(status) {
    switch(status) {
        case 'reviewing': return 'reviewing';
        case 'registered': return 'registered';
        case 'materials_uploaded': return 'materials-uploaded';
        default: return 'pending';
    }
}

// 获取参赛状态文本
function getRegistrationStatusText(status) {
    switch(status) {
        case 'reviewing': return '审核中';
        case 'registered': return '已报名';
        case 'materials_uploaded': return '已上传材料';
        case 'pending': return '待审核';
        default: return status || '未知';
    }
}

// 加载学生列表
async function loadStudents() {
    try {
        const response = await fetch(`${API_BASE}/students`);
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.querySelector('#studentsTable tbody');
            tbody.innerHTML = '';
            
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state">暂无学生数据，点击"添加学生"开始</td></tr>';
            } else {
                result.data.forEach(student => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${escapeHtml(student.name)}</td>
                        <td>${escapeHtml(student.grade || '未填写')}</td>
                        <td>${escapeHtml(student.major || '未填写')}</td>
                        <td class="text-mono">${escapeHtml(student.phone || '未填写')}</td>
                        <td>${escapeHtml(student.email || '未填写')}</td>
                        <td class="text-mono">${escapeHtml(student.password || '未填写')}</td>
                        <td>
                            <button class="btn btn-sm btn-ghost" onclick="editStudent(${student.id})">编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteStudent(${student.id})">删除</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        }
    } catch (error) {
        showToast('加载学生列表失败', 'error');
        console.error('加载学生列表失败:', error);
    }
}

// 加载采集数据（资讯中心）
async function loadCollectedData() {
    try {
        const grid = document.getElementById('newsGrid');
        grid.innerHTML = '<div class="news-loading">加载中...</div>';

        const response = await fetch(`${API_BASE}/collected-data`);
        const result = await response.json();

        if (result.success) {
            if (!result.data || result.data.length === 0) {
                grid.innerHTML = `
                    <div class="news-empty">
                        <div class="news-empty-icon">&#128240;</div>
                        <p>暂无资讯数据</p>
                        <p style="font-size:12px;opacity:0.6">点击"立即采集"从各赛事官网获取最新资讯</p>
                    </div>`;
                return;
            }

            grid.innerHTML = '';
            let allExpanded = result.data.length <= 3;

            result.data.forEach((group, idx) => {
                const hasNews = group.news && group.news.length > 0;
                const card = document.createElement('div');
                card.className = 'news-competition-card';

                const header = document.createElement('div');
                header.className = allExpanded ? 'news-competition-header' : 'news-competition-header collapsed';
                header.innerHTML = `
                    <h4>
                        ${escapeHtml(group.competition_name)}
                        <span class="news-count">${hasNews ? group.news.length : 0} 条资讯</span>
                    </h4>
                    <span class="expand-icon">${allExpanded ? '&#9660;' : '&#9660;'}</span>
                `;

                const list = document.createElement('div');
                list.className = allExpanded ? 'news-list' : 'news-list hidden';

                if (hasNews) {
                    group.news.forEach(item => {
                        const newsItem = document.createElement('div');
                        newsItem.className = 'news-item';
                        newsItem.innerHTML = `
                            <div class="news-item-title">${escapeHtml(item.title)}</div>
                            <div class="news-item-meta">
                                <span>${formatDate(item.publish_date || item.collected_at)}</span>
                                ${item.source_url ? `<a href="${escapeHtml(item.source_url)}" target="_blank" class="news-source" onclick="event.stopPropagation()">查看原文</a>` : ''}
                            </div>
                            ${item.summary ? `<div class="news-item-summary">${escapeHtml(item.summary)}</div>` : ''}
                        `;
                        newsItem.addEventListener('click', () => showNewsDetail(item));
                        list.appendChild(newsItem);
                    });
                } else {
                    list.innerHTML = '<div style="padding:16px 20px;color:var(--fog-grey);font-size:12px;text-align:center;">暂无资讯</div>';
                }

                header.addEventListener('click', () => {
                    header.classList.toggle('collapsed');
                    list.classList.toggle('hidden');
                });

                card.appendChild(header);
                card.appendChild(list);
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = `<div class="news-empty"><p>加载失败: ${escapeHtml(result.message || '未知错误')}</p></div>`;
        }
    } catch (error) {
        showToast('加载资讯失败', 'error');
        console.error('加载资讯失败:', error);
        document.getElementById('newsGrid').innerHTML = '<div class="news-empty"><p>加载失败，请检查网络连接</p></div>';
    }
}

// 显示资讯详情
function showNewsDetail(item) {
    document.getElementById('newsModalTitle').textContent = item.title || '资讯详情';
    const body = document.getElementById('newsModalBody');
    body.innerHTML = `
        <div class="news-detail-meta">
            <span>${formatDate(item.publish_date || item.collected_at)}</span>
            ${item.source_url ? `<a href="${escapeHtml(item.source_url)}" target="_blank">查看原文</a>` : ''}
            ${item.competition_name ? `<span>来源: ${escapeHtml(item.competition_name)}</span>` : ''}
        </div>
        <div class="news-detail-content">${escapeHtml(item.content || item.summary || item.title || '暂无详细内容')}</div>
    `;
    document.getElementById('newsModal').classList.add('active');
}

// 关闭资讯详情
document.getElementById('newsModalClose')?.addEventListener('click', () => {
    document.getElementById('newsModal').classList.remove('active');
});
document.getElementById('newsModalCloseBtn')?.addEventListener('click', () => {
    document.getElementById('newsModal').classList.remove('active');
});
document.getElementById('newsModal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('newsModal')) {
        document.getElementById('newsModal').classList.remove('active');
    }
});

// 加载日志
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs?limit=100`);
        const result = await response.json();
        
        if (result.success) {
            const logList = document.getElementById('logList');
            logList.innerHTML = '';
            
            if (result.data.length === 0) {
                logList.innerHTML = '<div class="empty-state">暂无日志记录</div>';
            } else {
                result.data.forEach(log => {
                    const logItem = document.createElement('div');
                    logItem.className = 'log-item';
                    logItem.innerHTML = `
                        <span class="log-level ${log.level.toLowerCase()}">${log.level}</span>
                        <div class="log-content">
                            <div class="log-message">${escapeHtml(log.message)}</div>
                            <div class="log-meta">
                                ${log.module ? `模块: ${escapeHtml(log.module)} | ` : ''}
                                时间: ${formatDate(log.created_at)}
                            </div>
                        </div>
                    `;
                    logList.appendChild(logItem);
                });
            }
        }
    } catch (error) {
        showToast('加载日志失败', 'error');
        console.error('加载日志失败:', error);
    }
}

// 触发数据采集
async function triggerCollection() {
    try {
        showToast('正在采集数据，请稍候...', 'info');
        const response = await fetch(`${API_BASE}/collect`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            showToast(`采集成功: ${result.message}`, 'success');
            loadDashboard();
            if (currentPage === 'data') {
                loadCollectedData();
            }
        } else {
            showToast(`采集失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast('采集数据失败', 'error');
        console.error('采集数据失败:', error);
    }
}

// 显示竞赛模态框
function showCompetitionModal(competition = null) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = competition ? '编辑竞赛' : '添加竞赛';
    
    modalBody.innerHTML = `
        <form id="competitionForm">
            <div class="form-group">
                <label for="compName">竞赛名称 *</label>
                <input type="text" id="compName" required value="${competition ? escapeHtml(competition.name) : ''}">
            </div>
            <div class="form-group">
                <label for="compUrl">官网链接</label>
                <input type="url" id="compUrl" value="${competition ? escapeHtml(competition.official_url || '') : ''}">
            </div>
            <div class="form-group">
                <label for="compDesc">描述</label>
                <textarea id="compDesc" rows="3">${competition ? escapeHtml(competition.description || '') : ''}</textarea>
            </div>
            <div class="form-group">
                <label for="compCategory">类别</label>
                <input type="text" id="compCategory" value="${competition ? escapeHtml(competition.category || '') : ''}">
            </div>
            <div class="form-group">
                <label for="compStatus">状态</label>
                <select id="compStatus">
                    <option value="active" ${competition && competition.status === 'active' ? 'selected' : ''}>进行中</option>
                    <option value="upcoming" ${competition && competition.status === 'upcoming' ? 'selected' : ''}>即将开始</option>
                    <option value="completed" ${competition && competition.status === 'completed' ? 'selected' : ''}>已结束</option>
                </select>
            </div>
            <div class="form-group">
                <label for="compStartDate">开始日期</label>
                <input type="date" id="compStartDate" value="${competition ? competition.start_date || '' : ''}">
            </div>
            <div class="form-group">
                <label for="compEndDate">结束日期</label>
                <input type="date" id="compEndDate" value="${competition ? competition.end_date || '' : ''}">
            </div>
            <div class="form-group">
                <label for="compMaterials">官方材料 (JSON格式，可选)</label>
                <textarea id="compMaterials" rows="3" placeholder='[{"name":"材料名称","url":"https://..."}]'>${competition ? escapeHtml(competition.official_materials || '') : ''}</textarea>
                <span class="form-hint">格式: [{"name":"参赛指南","url":"https://..."},{"name":"邀请函","url":"https://..."}]</span>
            </div>
        </form>
    `;
    
    modal.classList.add('active');
    
    document.getElementById('modalConfirm').onclick = async () => {
        const name = document.getElementById('compName').value.trim();
        if (!name) {
            showToast('请输入竞赛名称', 'warning');
            return;
        }
        
        const data = {
            name: name,
            official_url: document.getElementById('compUrl').value.trim(),
            description: document.getElementById('compDesc').value.trim(),
            category: document.getElementById('compCategory').value.trim(),
            official_materials: document.getElementById('compMaterials').value.trim(),
            status: document.getElementById('compStatus').value,
            start_date: document.getElementById('compStartDate').value,
            end_date: document.getElementById('compEndDate').value
        };
        
        try {
            const url = competition ? `${API_BASE}/competitions/${competition.id}` : `${API_BASE}/competitions`;
            const method = competition ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast(competition ? '竞赛更新成功' : '竞赛创建成功', 'success');
                closeModal();
                loadCompetitions();
                loadDashboard();
            } else {
                showToast(`操作失败: ${result.message}`, 'error');
            }
        } catch (error) {
            showToast('操作失败', 'error');
            console.error('竞赛操作失败:', error);
        }
    };
}

// 显示学生模态框
function showStudentModal(student = null) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = student ? '编辑学生' : '添加学生';
    
    modalBody.innerHTML = `
        <form id="studentForm">
            <div class="form-group">
                <label for="studentName">姓名 *</label>
                <input type="text" id="studentName" required value="${student ? escapeHtml(student.name) : ''}">
            </div>
            <div class="form-group">
                <label for="studentGrade">年级</label>
                <input type="text" id="studentGrade" value="${student ? escapeHtml(student.grade || '') : ''}">
            </div>
            <div class="form-group">
                <label for="studentMajor">专业</label>
                <input type="text" id="studentMajor" value="${student ? escapeHtml(student.major || '') : ''}">
            </div>
            <div class="form-group">
                <label for="studentPhone">电话</label>
                <input type="tel" id="studentPhone" value="${student ? escapeHtml(student.phone || '') : ''}">
            </div>
            <div class="form-group">
                <label for="studentEmail">邮箱</label>
                <input type="email" id="studentEmail" value="${student ? escapeHtml(student.email || '') : ''}">
            </div>
            <div class="form-group">
                <label for="studentPassword">密码</label>
                <input type="text" id="studentPassword" value="${student ? escapeHtml(student.password || '') : ''}">
            </div>
        </form>
    `;
    
    modal.classList.add('active');
    
    document.getElementById('modalConfirm').onclick = async () => {
        const name = document.getElementById('studentName').value.trim();
        if (!name) {
            showToast('请输入学生姓名', 'warning');
            return;
        }
        
        const data = {
            name: name,
            grade: document.getElementById('studentGrade').value.trim(),
            major: document.getElementById('studentMajor').value.trim(),
            phone: document.getElementById('studentPhone').value.trim(),
            email: document.getElementById('studentEmail').value.trim(),
            password: document.getElementById('studentPassword').value.trim()
        };
        
        try {
            const url = student ? `${API_BASE}/students/${student.id}` : `${API_BASE}/students`;
            const method = student ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast(student ? '学生信息更新成功' : '学生创建成功', 'success');
                closeModal();
                loadStudents();
                loadDashboard();
            } else {
                showToast(`操作失败: ${result.message}`, 'error');
            }
        } catch (error) {
            showToast('操作失败', 'error');
            console.error('学生操作失败:', error);
        }
    };
}

// 编辑竞赛
async function editCompetition(id) {
    try {
        const response = await fetch(`${API_BASE}/competitions`);
        const result = await response.json();
        
        if (result.success) {
            const competition = result.data.find(c => c.id === id);
            if (competition) {
                showCompetitionModal(competition);
            }
        }
    } catch (error) {
        showToast('获取竞赛信息失败', 'error');
        console.error('获取竞赛信息失败:', error);
    }
}

// 删除竞赛
async function deleteCompetition(id) {
    if (!confirm('确定要删除这个竞赛吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/competitions/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            showToast('竞赛删除成功', 'success');
            loadCompetitions();
            loadDashboard();
        } else {
            showToast(`删除失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
        console.error('删除竞赛失败:', error);
    }
}

// 编辑学生
async function editStudent(id) {
    try {
        const response = await fetch(`${API_BASE}/students`);
        const result = await response.json();
        
        if (result.success) {
            const student = result.data.find(s => s.id === id);
            if (student) {
                showStudentModal(student);
            }
        }
    } catch (error) {
        showToast('获取学生信息失败', 'error');
        console.error('获取学生信息失败:', error);
    }
}

// 删除学生
async function deleteStudent(id) {
    if (!confirm('确定要删除这个学生吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/students/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            showToast('学生删除成功', 'success');
            loadStudents();
            loadDashboard();
        } else {
            showToast(`删除失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
        console.error('删除学生失败:', error);
    }
}

// 关闭模态框
function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

// 显示提示消息
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '未填写';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'active': '进行中',
        'upcoming': '即将开始',
        'completed': '已结束'
    };
    return statusMap[status] || status;
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeUrl(url) {
    if (!url) return '';
    if (/^https?:\/\//i.test(url)) return url;
    return '#' + escapeHtml(url);
}

// 显示学生竞赛关联模态框
function showStudentCompetitionModal(relation = null, competitionId = null) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = relation ? '编辑参赛信息' : '添加参赛学生';
    
    // 获取学生和竞赛列表
    fetch(`${API_BASE}/students`)
        .then(res => res.json())
        .then(studentsResult => {
            fetch(`${API_BASE}/competitions`)
                .then(res => res.json())
                .then(competitionsResult => {
                    const students = studentsResult.data || [];
                    const competitions = competitionsResult.data || [];
                    
                    let studentOptions = students.map(s => 
                        `<option value="${s.id}" ${relation && relation.student_id === s.id ? 'selected' : ''}>${escapeHtml(s.name)} (${escapeHtml(s.grade || '')} - ${escapeHtml(s.major || '')})</option>`
                    ).join('');
                    
                    let competitionOptions = competitions.map(c => 
                        `<option value="${c.id}" ${relation && relation.competition_id === c.id ? 'selected' : ''} ${competitionId === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`
                    ).join('');
                    
                    modalBody.innerHTML = `
                        <form id="studentCompetitionForm">
                            <div class="form-group">
                                <label for="scStudent">学生 *</label>
                                <select id="scStudent" required>
                                    <option value="">请选择学生</option>
                                    ${studentOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="scCompetition">竞赛 *</label>
                                <select id="scCompetition" required ${competitionId ? 'disabled' : ''}>
                                    <option value="">请选择竞赛</option>
                                    ${competitionOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="scProjectName">项目名称</label>
                                <input type="text" id="scProjectName" value="${relation ? escapeHtml(relation.project_name || '') : ''}">
                            </div>
                            <div class="form-group">
                                <label for="scRole">角色</label>
                                <select id="scRole">
                                    <option value="队长" ${relation && relation.role === '队长' ? 'selected' : ''}>队长</option>
                                    <option value="队员" ${relation && relation.role === '队员' ? 'selected' : ''}>队员</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="scStatus">参赛状态 *</label>
                                <select id="scStatus">
                                    <option value="pending" ${relation && relation.registration_status === 'pending' ? 'selected' : ''}>待审核</option>
                                    <option value="reviewing" ${relation && relation.registration_status === 'reviewing' ? 'selected' : ''}>审核中</option>
                                    <option value="registered" ${relation && relation.registration_status === 'registered' ? 'selected' : ''}>已报名</option>
                                    <option value="materials_uploaded" ${relation && relation.registration_status === 'materials_uploaded' ? 'selected' : ''}>已上传材料</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="scRemarks">备注</label>
                                <textarea id="scRemarks" rows="3">${relation ? escapeHtml(relation.remarks || '') : ''}</textarea>
                            </div>
                        </form>
                    `;
                    
                    modal.classList.add('active');
                    
                    document.getElementById('modalConfirm').onclick = async () => {
                        const studentId = document.getElementById('scStudent').value;
                        const compId = competitionId || document.getElementById('scCompetition').value;
                        
                        if (!studentId || !compId) {
                            showToast('请选择学生和竞赛', 'warning');
                            return;
                        }
                        
                        const data = {
                            student_id: parseInt(studentId),
                            competition_id: parseInt(compId),
                            project_name: document.getElementById('scProjectName').value.trim(),
                            role: document.getElementById('scRole').value,
                            registration_status: document.getElementById('scStatus').value,
                            remarks: document.getElementById('scRemarks').value.trim()
                        };
                        
                        try {
                            const url = relation ? `${API_BASE}/student-competitions/${relation.id}` : `${API_BASE}/student-competitions`;
                            const method = relation ? 'PUT' : 'POST';
                            
                            const response = await fetch(url, {
                                method: method,
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(data)
                            });
                            
                            const result = await response.json();
                            
                            if (result.success) {
                                showToast(relation ? '参赛信息更新成功' : '参赛学生添加成功', 'success');
                                closeModal();
                                if (currentCompetitionId) {
                                    viewCompetitionDetail(currentCompetitionId);
                                }
                                loadCompetitions();
                            } else {
                                showToast(`操作失败: ${result.message}`, 'error');
                            }
                        } catch (error) {
                            showToast('操作失败', 'error');
                            console.error('参赛信息操作失败:', error);
                        }
                    };
                });
        });
}

// 编辑学生竞赛关联
async function editStudentCompetition(relationId) {
    try {
        const response = await fetch(`${API_BASE}/student-competitions`);
        const result = await response.json();
        
        if (result.success) {
            const relation = result.data.find(r => r.id === relationId);
            if (relation) {
                showStudentCompetitionModal(relation);
            }
        }
    } catch (error) {
        showToast('获取参赛信息失败', 'error');
        console.error('获取参赛信息失败:', error);
    }
}

// 删除学生竞赛关联
async function deleteStudentCompetition(relationId) {
    if (!confirm('确定要删除这个参赛记录吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/student-competitions/${relationId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            showToast('参赛记录删除成功', 'success');
            if (currentCompetitionId) {
                viewCompetitionDetail(currentCompetitionId);
            }
            loadCompetitions();
        } else {
            showToast(`删除失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
        console.error('删除参赛记录失败:', error);
    }
}

// 上传材料
function uploadMaterial(relationId) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = '上传项目材料';
    modalBody.innerHTML = `
        <form id="uploadForm">
            <div class="form-group">
                <label for="materialFile">选择文件 *</label>
                <input type="file" id="materialFile" required>
                <p class="text-muted" style="margin-top: 8px; font-size: 12px;">支持格式: PDF, DOC, DOCX, ZIP, RAR, 7Z, PNG, JPG (最大50MB)</p>
            </div>
        </form>
    `;
    
    modal.classList.add('active');
    
    document.getElementById('modalConfirm').onclick = async () => {
        const fileInput = document.getElementById('materialFile');
        if (!fileInput.files || fileInput.files.length === 0) {
            showToast('请选择文件', 'warning');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            showToast('正在上传...', 'info');
            const response = await fetch(`${API_BASE}/upload-material/${relationId}`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast('材料上传成功', 'success');
                closeModal();
                if (currentCompetitionId) {
                    viewCompetitionDetail(currentCompetitionId);
                }
            } else {
                showToast(`上传失败: ${result.message}`, 'error');
            }
        } catch (error) {
            showToast('上传失败', 'error');
            console.error('上传材料失败:', error);
        }
    };
}

// ==================== 文件浏览器 ====================
let fileBrowserCurrentPath = '';
let fileBrowserCompetitionId = null;

function initFileBrowser(competitionId) {
    fileBrowserCompetitionId = competitionId;
    fileBrowserCurrentPath = '';

    const sidebarLinks = document.querySelectorAll('#fileBrowserSidebar .sidebar-quick-link');
    sidebarLinks.forEach(link => {
        link.onclick = () => {
            sidebarLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            browseCompetitionFiles(link.dataset.path);
        };
    });

    browseCompetitionFiles('');
}

async function browseCompetitionFiles(subdir) {
    if (!fileBrowserCompetitionId) return;

    const content = document.getElementById('fileBrowserContent');
    content.innerHTML = '<div class="loading-state">加载中...</div>';

    try {
        const params = new URLSearchParams({
            competition_id: fileBrowserCompetitionId,
            subdir: subdir
        });
        const response = await fetch(`${API_BASE}/files/browse?${params}`);
        const result = await response.json();

        if (!result.success) {
            content.innerHTML = `<div class="empty-state">${escapeHtml(result.message)}</div>`;
            return;
        }

        fileBrowserCurrentPath = result.data.current_path;
        renderFileBrowser(result.data);
    } catch (error) {
        content.innerHTML = '<div class="empty-state">加载失败</div>';
        console.error('文件浏览失败:', error);
    }
}

function renderFileBrowser(data) {
    const content = document.getElementById('fileBrowserContent');
    const breadcrumb = document.getElementById('fileBreadcrumb');

    const pathParts = data.current_path ? data.current_path.split('/') : [];
    breadcrumb.innerHTML = '<span class="breadcrumb-item" onclick="browseCompetitionFiles(\'\')">📁 根目录</span>';
    let cumPath = '';
    pathParts.forEach((part, i) => {
        cumPath += (cumPath ? '/' : '') + part;
        const safePath = escapeHtml(cumPath).replace(/'/g, "\\'");
        breadcrumb.innerHTML += `
            <span class="breadcrumb-sep">/</span>
            <span class="breadcrumb-item" onclick="browseCompetitionFiles('${safePath}')">${escapeHtml(part)}</span>
        `;
    });

    if (!data.items || data.items.length === 0) {
        content.innerHTML = '<div class="empty-state">此目录为空</div>';
        return;
    }

    let html = '<div class="file-grid">';
    data.items.forEach(item => {
        const icon = item.type === 'folder' ? '📁' : getFileIcon(item.name);
        const sizeText = item.size ? formatFileSize(item.size) : '';
        const safeName = escapeHtml(item.name).replace(/'/g, "\\'");
        const safePath = escapeHtml(item.path).replace(/'/g, "\\'");

        const clickAction = item.type === 'folder'
            ? `browseCompetitionFiles('${safePath}')`
            : `openFile('${encodeURIComponent(item.path)}')`;

        html += `
            <div class="file-item ${item.type}" 
                 onclick="${clickAction}"
                 title="${safeName}">
                <div class="file-icon">${icon}</div>
                <div class="file-name">${safeName}</div>
                <div class="file-meta">${sizeText}</div>
                <div class="file-actions">
                    <button class="btn btn-sm btn-ghost" onclick="event.stopPropagation(); downloadFile('${encodeURIComponent(item.path)}')" title="下载">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';

    content.innerHTML = html;
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': '📄', 'doc': '📝', 'docx': '📝', 'ppt': '📊', 'pptx': '📊',
        'xls': '📈', 'xlsx': '📈', 'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️',
        'gif': '🖼️', 'svg': '🖼️', 'bmp': '🖼️', 'webp': '🖼️',
        'py': '🐍', 'js': '📜', 'ts': '📜', 'html': '🌐', 'css': '🎨',
        'json': '⚙️', 'xml': '⚙️', 'yml': '⚙️', 'yaml': '⚙️',
        'zip': '📦', 'rar': '📦', '7z': '📦', 'gz': '📦',
        'md': '📋', 'txt': '📃', 'csv': '📊',
        'cpp': '⚡', 'c': '⚡', 'h': '⚡', 'java': '☕',
        'mp4': '🎬', 'mp3': '🎵', 'wav': '🎵',
    };
    return iconMap[ext] || '📎';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function openFile(filePath) {
    const url = `${API_BASE}/files/serve/${fileBrowserCompetitionId}?path=${filePath}`;
    window.open(url, '_blank');
}

function downloadFile(filePath) {
    const url = `${API_BASE}/files/serve/${fileBrowserCompetitionId}?path=${filePath}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = filePath.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
