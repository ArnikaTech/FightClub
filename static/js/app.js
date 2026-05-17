/* ============================================================
APP.JS
============================================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // ۱. ذرات شناور (landing)
    // ============================================================
    var particlesContainer = document.getElementById('particlesContainer');
    if (particlesContainer) {
        var colors = ['#ff4d2e', '#ffb800', '#ffffff', '#ff8a65'];
        for (var i = 0; i < 30; i++) {
            var p = document.createElement('div');
            p.classList.add('particle');
            var size = Math.random() * 4 + 2;
            var color = colors[Math.floor(Math.random() * colors.length)];
            p.style.cssText = 
            'width:' + size + 'px;' +
            'height:' + size + 'px;' +
            'left:' + (Math.random() * 100) + '%;' +
            'background:' + color + ';' +
            'animation-duration:' + (Math.random() * 8 + 6) + 's;' +
            'animation-delay:' + (Math.random() * 6) + 's;' +
            'box-shadow:0 0 ' + (size * 2) + 'px ' + color + ';';
            particlesContainer.appendChild(p);
        }
    }
    
    // ============================================================
    // ۲. ripple دکمه ورود (landing)
    // ============================================================
    var btnEnter = document.getElementById('btnEnter');
    if (btnEnter) {
        if (!document.getElementById('rippleKeyframes')) {
            var style = document.createElement('style');
            style.id = 'rippleKeyframes';
            style.textContent = '@keyframes rippleEffect{to{transform:scale(4);opacity:0}}';
            document.head.appendChild(style);
        }
        btnEnter.addEventListener('click', function(e) {
            e.preventDefault();
            var ripple = document.createElement('span');
            ripple.style.cssText = 
            'position:absolute;border-radius:50%;' +
            'background:rgba(255,255,255,0.5);' +
            'transform:scale(0);' +
            'animation:rippleEffect 0.7s ease-out;' +
            'pointer-events:none;';
            var rect = btnEnter.getBoundingClientRect();
            var size = Math.max(rect.width, rect.height);
            ripple.style.width = size + 'px';
            ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
            btnEnter.appendChild(ripple);
            setTimeout(function() {
                ripple.remove();
                window.location.href = btnEnter.href;
            }, 400);
        });
    }
    
    // ============================================================
    // ۳. لاگین
    // ============================================================
    var toggleBtn = document.getElementById('togglePassword');
    var passwordInput = document.getElementById('password');
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var icon = this.querySelector('i');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.replace('bi-eye-slash', 'bi-eye');
                this.style.color = '#ffb800';
            } else {
                passwordInput.type = 'password';
                icon.classList.replace('bi-eye', 'bi-eye-slash');
                this.style.color = '';
            }
        });
    }
    
    var phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            var v = this.value.replace(/\D/g, '');
            if (v.length > 11) v = v.slice(0, 11);
            this.value = v;
        });
    }
    
    document.addEventListener('gesturestart', function(e) { e.preventDefault(); });
    
    var loginForm = document.getElementById('loginForm');
    var loginSubmit = document.getElementById('btnSubmit');
    var loginError = document.getElementById('errorMessage');
    if (loginForm && loginSubmit) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (loginError) loginError.classList.add('d-none');
            var phone = phoneInput ? phoneInput.value.trim() : '';
            var pass = passwordInput ? passwordInput.value.trim() : '';
            if (!phone || phone.length < 10) {
                showLoginError('شماره موبایل معتبر وارد کنید', phoneInput);
                return;
            }
            if (!pass || pass.length < 4) {
                showLoginError('رمز عبور حداقل ۴ کاراکتر باشد', passwordInput);
                return;
            }
            loginSubmit.classList.add('loading');
            setTimeout(function() {
                loginSubmit.classList.remove('loading');
                loginForm.submit();
            }, 1500);
        });
    }
    
    function showLoginError(msg, el) {
        if (loginError) {
            loginError.querySelector('span').textContent = msg;
            loginError.classList.remove('d-none');
            loginError.classList.add('animate__animated', 'animate__shakeX');
            setTimeout(function() { loginError.classList.remove('animate__animated', 'animate__shakeX'); }, 500);
        }
        if (el) {
            el.style.borderColor = '#ff4d2e';
            el.classList.add('animate__animated', 'animate__shakeX');
            setTimeout(function() {
                el.style.borderColor = '';
                el.classList.remove('animate__animated', 'animate__shakeX');
            }, 500);
            el.focus();
        }
    }
    
    // ============================================================
    // ۴. تم تاریک/روشن
    // ============================================================
    var themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-mode');
        }
        themeBtn.addEventListener('click', function() {
            document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
        });
    }
    
    // ============================================================
    // ۵. همبرگر منو
    // ============================================================
    var hamburger = document.getElementById('hamburgerBtn');
    var mobileOverlay = document.getElementById('mobileNavOverlay');
    var mobileNav = document.getElementById('mobileNav');
    var navClose = document.getElementById('navClose');
    function openMobileNav() {
        if (mobileOverlay) mobileOverlay.classList.add('show');
        if (mobileNav) mobileNav.classList.add('show');
    }
    function closeMobileNav() {
        if (mobileOverlay) mobileOverlay.classList.remove('show');
        if (mobileNav) mobileNav.classList.remove('show');
    }
    if (hamburger) hamburger.addEventListener('click', openMobileNav);
    if (navClose) navClose.addEventListener('click', closeMobileNav);
    if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileNav);
    
    // ============================================================
    // ۶. آکاردئون منوی موبایل (فقط یکی باز باشه)
    // ============================================================
    document.querySelectorAll('.nav-group-header').forEach(function(header) {
        header.addEventListener('click', function() {
            var group = this.parentElement;
            var wasOpen = group.classList.contains('open');
            document.querySelectorAll('.nav-group').forEach(function(g) { g.classList.remove('open'); });
            if (!wasOpen) group.classList.add('open');
        });
    });
    
    // ============================================================
    // ۷. Bottom Sheet
    // ============================================================
    var moreBtn = document.getElementById('moreBtn');
    var bsOverlay = document.getElementById('bottomSheetOverlay');
    var bsSheet = document.getElementById('bottomSheet');
    if (moreBtn) {
        moreBtn.addEventListener('click', function(e) {
            e.preventDefault();
            bsOverlay.classList.add('show');
            bsSheet.classList.add('show');
        });
    }
    if (bsOverlay) {
        bsOverlay.addEventListener('click', function() {
            bsOverlay.classList.remove('show');
            bsSheet.classList.remove('show');
        });
    }
    
    // ============================================================
    // ۸. Toast عمومی
    // ============================================================
    window.toastTimer = null;
    window.showToast = function(iconClass, color, text, sub) {
        var toast = document.getElementById('customToast');
        if (!toast) return;
        var icon = toast.querySelector('.toast-icon');
        var t = toast.querySelector('.toast-text');
        var s = toast.querySelector('.toast-sub');
        icon.innerHTML = '<i class="bi ' + iconClass + '"></i>';
        icon.className = 'toast-icon ' + color;
        t.textContent = text;
        s.textContent = sub || '';
        clearTimeout(window.toastTimer);
        toast.classList.add('show');
        window.toastTimer = setTimeout(function() { toast.classList.remove('show'); }, 2000);
    };
    
    // ============================================================
    // ۹. پروفایل - ویرایش
    // ============================================================
    var btnEditProfile = document.getElementById('btnEditProfile');
    var btnChangePassword = document.getElementById('btnChangePassword');
    
    if (btnEditProfile) {
        btnEditProfile.addEventListener('click', function() {
            document.getElementById('editProfileOverlay').classList.add('show');
            document.getElementById('editProfileModal').classList.add('show');
        });
    }
    if (btnChangePassword) {
        btnChangePassword.addEventListener('click', function() {
            document.getElementById('passwordOverlay').classList.add('show');
            document.getElementById('passwordModal').classList.add('show');
        });
    }
    
    var btnCancelEdit = document.getElementById('btnCancelEdit');
    if (btnCancelEdit) {
        btnCancelEdit.addEventListener('click', function() {
            document.getElementById('editProfileOverlay').classList.remove('show');
            document.getElementById('editProfileModal').classList.remove('show');
        });
    }
    document.getElementById('editProfileOverlay')?.addEventListener('click', function() {
        this.classList.remove('show');
        document.getElementById('editProfileModal').classList.remove('show');
    });
    
    var btnSaveEdit = document.getElementById('btnSaveEdit');
    if (btnSaveEdit) {
        btnSaveEdit.addEventListener('click', function() {
            var name = document.getElementById('editName')?.value.trim() || '';
            var phone = document.getElementById('editPhone')?.value.trim() || '';
            var bio = document.getElementById('editBio')?.value.trim() || '';
            if (!name) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'نام الزامی است'); return; }
            document.getElementById('displayName').textContent = name;
            document.getElementById('displayFullName').textContent = name;
            document.getElementById('displayNameHeader').textContent = name;
            document.getElementById('displayPhone').textContent = phone;
            document.getElementById('displayPhoneHeader').innerHTML = '<i class="bi bi-phone"></i> ' + phone;
            document.getElementById('displayBio').textContent = bio || 'وارد نشده';
            document.getElementById('editProfileOverlay').classList.remove('show');
            document.getElementById('editProfileModal').classList.remove('show');
            showToast('bi-check-circle-fill', 'green', 'ذخیره شد', 'پروفایل بروزرسانی شد');
        });
    }
    
    var btnCancelPassword = document.getElementById('btnCancelPassword');
    if (btnCancelPassword) {
        btnCancelPassword.addEventListener('click', function() {
            document.getElementById('passwordOverlay').classList.remove('show');
            document.getElementById('passwordModal').classList.remove('show');
        });
    }
    document.getElementById('passwordOverlay')?.addEventListener('click', function() {
        this.classList.remove('show');
        document.getElementById('passwordModal').classList.remove('show');
    });
    
    var btnSavePassword = document.getElementById('btnSavePassword');
    if (btnSavePassword) {
        btnSavePassword.addEventListener('click', function() {
            var current = document.getElementById('currentPassword')?.value || '';
            var newPass = document.getElementById('newPassword')?.value || '';
            var confirm = document.getElementById('confirmPassword')?.value || '';
            if (!current) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'رمز فعلی را وارد کنید'); return; }
            if (!newPass || newPass.length < 6) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'رمز جدید حداقل ۶ کاراکتر'); return; }
            if (newPass !== confirm) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'رمزها مطابقت ندارند'); return; }
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
            document.getElementById('passwordOverlay').classList.remove('show');
            document.getElementById('passwordModal').classList.remove('show');
            showToast('bi-check-circle-fill', 'green', 'انجام شد', 'رمز عبور تغییر کرد');
        });
    }
    
    // ============================================================
    // ۱۰. اطلاعات باشگاه - ویرایش
    // ============================================================
    var btnEditGym = document.getElementById('btnEditGym');
    if (btnEditGym) {
        btnEditGym.addEventListener('click', function() {
            document.getElementById('editGymOverlay').classList.add('show');
            document.getElementById('editGymModal').classList.add('show');
        });
    }
    document.getElementById('btnCancelEditGym')?.addEventListener('click', function() {
        document.getElementById('editGymOverlay').classList.remove('show');
        document.getElementById('editGymModal').classList.remove('show');
    });
    document.getElementById('editGymOverlay')?.addEventListener('click', function() {
        this.classList.remove('show');
        document.getElementById('editGymModal').classList.remove('show');
    });
    var btnSaveEditGym = document.getElementById('btnSaveEditGym');
    if (btnSaveEditGym) {
        btnSaveEditGym.addEventListener('click', function() {
            var name = document.getElementById('editGymName')?.value.trim() || '';
            var city = document.getElementById('editGymCity')?.value.trim() || '';
            var address = document.getElementById('editGymAddress')?.value.trim() || '';
            var phone = document.getElementById('editGymPhone')?.value.trim() || '';
            if (!name) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'نام باشگاه الزامی است'); return; }
            document.getElementById('gymNameDisplay').textContent = name;
            document.getElementById('gymCityDisplay').textContent = city;
            document.getElementById('gymName').textContent = name;
            document.getElementById('gymCity').textContent = city;
            document.getElementById('gymAddress').textContent = address || '-';
            document.getElementById('gymPhone').textContent = phone || '-';
            document.getElementById('editGymOverlay').classList.remove('show');
            document.getElementById('editGymModal').classList.remove('show');
            showToast('bi-check-circle-fill', 'green', 'ذخیره شد', 'اطلاعات باشگاه بروزرسانی شد');
        });
    }
    
    // ============================================================
    // ۱۱. ثبت حضور (attendance)
    // ============================================================
    var attList = document.getElementById('attendanceList');
    if (attList) {
        var totalItems = document.querySelectorAll('.attendance-item').length;
        updateAttendanceCounts();
        
        attList.addEventListener('click', function(e) {
            var item = e.target.closest('.attendance-item');
            if (!item) return;
            if (e.target.closest('.btn-call')) return;
            item.classList.toggle('checked');
            updateAttendanceCounts();
            var name = item.getAttribute('data-name');
            if (item.classList.contains('checked')) {
                showToast('bi-check-circle-fill', 'green', name, 'حضور ثبت شد');
            } else {
                showToast('bi-x-circle-fill', 'red', name, 'حضور لغو شد');
            }
        });
        
        function updateAttendanceCounts() {
            var present = document.querySelectorAll('.attendance-item.checked').length;
            var total = totalItems;
            var absent = total - present;
            var birthdays = document.querySelectorAll('.attendance-item[data-birthday="true"]').length;
            document.getElementById('presentCount').textContent = present;
            document.getElementById('absentCount').textContent = absent;
            document.getElementById('birthdayCount').textContent = birthdays;
            document.getElementById('totalCount').textContent = total;
        }
        
        var btnSave = document.getElementById('btnSave');
        if (btnSave) {
            btnSave.addEventListener('click', function() {
                var present = document.querySelectorAll('.attendance-item.checked').length;
                showToast('bi-cloud-check', 'green', 'ذخیره شد', present + ' هنرجو حاضر');
            });
        }
    }
    
    // ============================================================
    // ۱۲. قالب‌های پیامک (sms_templates)
    // ============================================================
    document.querySelectorAll('.btn-toggle').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var card = this.closest('.template-card');
            if (!card) return;
            var status = card.querySelector('.template-status');
            if (this.classList.contains('on')) {
                this.classList.remove('on'); this.classList.add('off');
                this.textContent = 'غیرفعال';
                if (status) { status.className = 'template-status inactive'; status.textContent = 'غیرفعال'; }
            } else {
                this.classList.remove('off'); this.classList.add('on');
                this.textContent = 'فعال';
                if (status) { status.className = 'template-status active'; status.textContent = 'فعال'; }
            }
        });
    });
    
    var btnAddTemplate = document.getElementById('btnAddTemplate');
    if (btnAddTemplate) {
        btnAddTemplate.addEventListener('click', function() {
            document.getElementById('modalOverlay').classList.add('show');
            document.getElementById('modalSheet').classList.add('show');
        });
    }
    document.getElementById('btnCancelTemplate')?.addEventListener('click', function() {
        document.getElementById('modalOverlay').classList.remove('show');
        document.getElementById('modalSheet').classList.remove('show');
    });
    document.getElementById('modalOverlay')?.addEventListener('click', function() {
        this.classList.remove('show');
        document.getElementById('modalSheet').classList.remove('show');
    });
    
    // ============================================================
    // ۱۳. ارسال پیامک (sms_send)
    // ============================================================
    var memberCheckList = document.getElementById('memberCheckList');
    if (memberCheckList) {
        memberCheckList.addEventListener('click', function(e) {
            var item = e.target.closest('.member-check-item');
            if (!item) return;
            item.classList.toggle('checked');
            updateSmsCount();
        });
        
        function updateSmsCount() {
            var count = document.querySelectorAll('#memberCheckList .member-check-item.checked').length;
            var sc = document.getElementById('selectedCount');
            if (sc) sc.textContent = count;
        }
        
        var selectAllBtn = document.getElementById('selectAllBtn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', function() {
                var items = document.querySelectorAll('#memberCheckList .member-check-item');
                var allChecked = true;
                items.forEach(function(item) { if (!item.classList.contains('checked')) allChecked = false; });
                items.forEach(function(item) {
                    if (allChecked) item.classList.remove('checked');
                    else item.classList.add('checked');
                });
                updateSmsCount();
            });
        }
        
        var chipRow = document.getElementById('chipRow');
        if (chipRow) {
            chipRow.addEventListener('click', function(e) {
                var chip = e.target.closest('.chip-select');
                if (!chip) return;
                document.querySelectorAll('#chipRow .chip-select').forEach(function(c) { c.classList.remove('active'); });
                chip.classList.add('active');
                var group = chip.getAttribute('data-group');
                document.querySelectorAll('#memberCheckList .member-check-item').forEach(function(item) {
                    var itemGroup = item.getAttribute('data-group') || '';
                    if (group === 'all' || itemGroup.includes(group)) item.style.display = '';
                    else item.style.display = 'none';
                });
            });
        }
        
        var messageText = document.getElementById('messageText');
        var charCounter = document.getElementById('charCounter');
        if (messageText && charCounter) {
            messageText.addEventListener('input', function() { charCounter.textContent = this.value.length; });
        }
        
        var btnSend = document.getElementById('btnSend');
        if (btnSend) {
            btnSend.addEventListener('click', function() {
                var count = document.querySelectorAll('#memberCheckList .member-check-item.checked').length;
                var msg = messageText ? messageText.value.trim() : '';
                if (count === 0) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'هیچ مخاطبی انتخاب نشده'); return; }
                if (!msg) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'متن پیام خالی است'); return; }
                showToast('bi-check-circle-fill', 'green', 'ارسال شد', 'پیامک به ' + count + ' نفر ارسال شد');
            });
        }
    }
    
    // ============================================================
    // ۱۴. فیلتر چیپ‌ها (members)
    // ============================================================
    document.querySelectorAll('.filter-chip').forEach(function(chip) {
        chip.addEventListener('click', function() {
            document.querySelectorAll('.filter-chip').forEach(function(c) { c.classList.remove('active'); });
            this.classList.add('active');
        });
    });
    
    // ============================================================
    // ۱۵. مربیان (coaches)
    // ============================================================
    var btnAddCoach = document.getElementById('btnAddCoach');
    if (btnAddCoach) {
        btnAddCoach.addEventListener('click', function() {
            var coachId = document.getElementById('coachId'); if (coachId) coachId.value = '';
            var coachName = document.getElementById('coachName'); if (coachName) coachName.value = '';
            var coachPhone = document.getElementById('coachPhone'); if (coachPhone) coachPhone.value = '';
            var coachBelt = document.getElementById('coachBelt'); if (coachBelt) coachBelt.value = '';
            var coachRole = document.getElementById('coachRole'); if (coachRole) coachRole.value = 'مربی';
            var modalTitle = document.getElementById('coachModalTitle'); if (modalTitle) modalTitle.textContent = 'مربی جدید';
            document.getElementById('coachModalOverlay').classList.add('show');
            document.getElementById('coachModal').classList.add('show');
        });
    }
    
    document.getElementById('btnCancelCoach')?.addEventListener('click', function() {
        document.getElementById('coachModalOverlay').classList.remove('show');
        document.getElementById('coachModal').classList.remove('show');
    });
    document.getElementById('coachModalOverlay')?.addEventListener('click', function() {
        this.classList.remove('show');
        document.getElementById('coachModal').classList.remove('show');
    });
    
    var btnSaveCoach = document.getElementById('btnSaveCoach');
    if (btnSaveCoach) {
        btnSaveCoach.addEventListener('click', function() {
            var name = document.getElementById('coachName')?.value.trim() || '';
            var phone = document.getElementById('coachPhone')?.value.trim() || '';
            var belt = document.getElementById('coachBelt')?.value.trim() || '';
            var role = document.getElementById('coachRole')?.value || '';
            if (!name || !phone) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'نام و شماره تماس الزامی است'); return; }
            
            var id = document.getElementById('coachId')?.value || '';
            var coachList = document.getElementById('coachList');
            if (id) {
                var card = document.querySelector('.coach-card-page[data-id="' + id + '"]');
                if (card) {
                    card.querySelector('.coach-name-page').textContent = name;
                    card.querySelector('.coach-meta-page').innerHTML = '<span>' + role + '</span><span>کمربند ' + belt + '</span>';
                    card.setAttribute('data-name', name);
                    card.setAttribute('data-phone', phone);
                    card.setAttribute('data-belt', belt);
                    card.setAttribute('data-role', role);
                }
                showToast('bi-check-circle-fill', 'green', 'بروزرسانی شد', name);
            } else if (coachList) {
                var newId = Date.now();
                var html = '<div class="coach-card-page animate__animated animate__fadeInUp animate__faster" data-id="' + newId + '" data-name="' + name + '" data-phone="' + phone + '" data-belt="' + belt + '" data-role="' + role + '">' +
                '<div class="coach-avatar-page"><i class="bi bi-person-fill"></i></div>' +
                '<div class="coach-info-page"><div class="coach-name-page">' + name + '</div><div class="coach-meta-page"><span>' + role + '</span><span>کمربند ' + belt + '</span></div></div>' +
                '<div class="coach-actions">' +
                '<a href="tel:' + phone + '" class="coach-action-btn call"><i class="bi bi-telephone-fill"></i></a>' +
                '<button class="coach-action-btn edit" onclick="editCoach(this)" title="ویرایش"><i class="bi bi-pencil"></i></button>' +
                '<button class="coach-action-btn delete" onclick="deleteCoach(this)" title="حذف"><i class="bi bi-trash"></i></button>' +
                '</div></div>';
                coachList.insertAdjacentHTML('beforeend', html);
                showToast('bi-check-circle-fill', 'green', 'اضافه شد', name);
            }
            document.getElementById('coachModalOverlay').classList.remove('show');
            document.getElementById('coachModal').classList.remove('show');
        });
    }
    
    window.editCoach = function(btn) {
        var card = btn.closest('.coach-card-page');
        document.getElementById('coachId').value = card.getAttribute('data-id');
        document.getElementById('coachName').value = card.getAttribute('data-name');
        document.getElementById('coachPhone').value = card.getAttribute('data-phone');
        document.getElementById('coachBelt').value = card.getAttribute('data-belt');
        document.getElementById('coachRole').value = card.getAttribute('data-role');
        document.getElementById('coachModalTitle').textContent = 'ویرایش مربی';
        document.getElementById('coachModalOverlay').classList.add('show');
        document.getElementById('coachModal').classList.add('show');
    };
    
    window.deleteCoach = function(btn) {
        var card = btn.closest('.coach-card-page');
        var name = card.getAttribute('data-name');
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.8)';
        setTimeout(function() { card.remove(); }, 300);
        showToast('bi-check-circle-fill', 'green', 'حذف شد', name);
    };
    
    // ============================================================
    // ۱۶. ارتقا هنرجوها (belts_promotion)
    // ============================================================
    var promoList = document.getElementById('promotionList');
    if (promoList) {
        promoList.addEventListener('click', function(e) {
            var card = e.target.closest('.promotion-card');
            if (!card) return;
            card.classList.toggle('selected');
            if (card.classList.contains('selected')) {
                card.style.borderColor = 'var(--accent)';
                card.style.background = 'rgba(255,184,0,0.08)';
            } else {
                card.style.borderColor = '';
                card.style.background = '';
            }
        });
        
        var btnOpenAddModal = document.getElementById('btnOpenAddModal');
        if (btnOpenAddModal) {
            btnOpenAddModal.addEventListener('click', function() {
                document.querySelectorAll('#modalMemberList .modal-member-item').forEach(function(i) { i.classList.remove('checked'); });
                document.getElementById('addModalOverlay').classList.add('show');
                document.getElementById('addModal').classList.add('show');
            });
        }
        
        document.getElementById('btnCancelAdd')?.addEventListener('click', function() {
            document.getElementById('addModalOverlay').classList.remove('show');
            document.getElementById('addModal').classList.remove('show');
        });
        document.getElementById('addModalOverlay')?.addEventListener('click', function() {
            this.classList.remove('show');
            document.getElementById('addModal').classList.remove('show');
        });
        
        document.querySelectorAll('#modalMemberList .modal-member-item').forEach(function(item) {
            item.addEventListener('click', function() { this.classList.toggle('checked'); });
        });
        
        var btnConfirmAdd = document.getElementById('btnConfirmAdd');
        if (btnConfirmAdd) {
            btnConfirmAdd.addEventListener('click', function() {
                var selected = document.querySelectorAll('#modalMemberList .modal-member-item.checked');
                if (selected.length === 0) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'هیچ هنرجویی انتخاب نشده'); return; }
                var targetBelt = document.getElementById('targetBelt')?.value || '';
                selected.forEach(function(item) {
                    var name = item.getAttribute('data-name');
                    var currentBelt = item.getAttribute('data-current');
                    var age = item.getAttribute('data-age');
                    var sessions = item.getAttribute('data-sessions');
                    if (promoList.querySelector('.promotion-card[data-name="' + name + '"]')) return;
                    var html = '<div class="promotion-card animate__animated animate__fadeInUp animate__faster" data-name="' + name + '">' +
                    '<div class="promo-avatar"><i class="bi bi-person-fill"></i></div>' +
                    '<div class="promo-info"><div class="promo-name">' + name + '</div><div class="promo-meta"><span>' + age + ' سال</span><span>' + sessions + ' جلسه</span></div></div>' +
                    '<div class="promo-belt-change"><span class="belt-from">' + currentBelt + '</span><i class="bi bi-arrow-left"></i><span class="belt-to">' + targetBelt + '</span></div></div>';
                    promoList.insertAdjacentHTML('beforeend', html);
                });
                document.getElementById('addModalOverlay').classList.remove('show');
                document.getElementById('addModal').classList.remove('show');
                showToast('bi-check-circle-fill', 'green', 'اضافه شد', selected.length + ' هنرجو به لیست افزوده شدند');
            });
        }
        
        var btnPromote = document.getElementById('btnPromote');
        if (btnPromote) {
            btnPromote.addEventListener('click', function() {
                var selected = promoList.querySelectorAll('.promotion-card.selected');
                if (selected.length === 0) { showToast('bi-exclamation-circle-fill', 'red', 'خطا', 'هیچ هنرجویی انتخاب نشده'); return; }
                var count = selected.length;
                selected.forEach(function(card, index) {
                    setTimeout(function() {
                        card.style.transition = 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
                        card.style.transform = 'scale(0.85)';
                        card.style.opacity = '0';
                        card.style.marginBottom = '-' + card.offsetHeight + 'px';
                        card.style.padding = '0'; card.style.borderWidth = '0';
                        setTimeout(function() { card.remove(); }, 350);
                    }, index * 80);
                });
                showToast('bi-check-circle-fill', 'green', 'ارتقا ثبت شد', count + ' هنرجو ارتقا یافتند');
            });
        }
    }
    
});