import request from '@/utils/request'

// 登录方法
export function login(username, password) {
    const data = {
        username,
        password,

    }
    return request({
        url: '/login',
        headers: {
            isToken: false,

            'Authorization': `Basic ${btoa(username + ":" + password)}`

        },
        method: 'post',
        data: data
    })
}

// 注册方法
export function register(data) {
    return request({
        url: '/register',
        headers: {
            isToken: false
        },
        method: 'post',
        data: data
    })
}

// 获取用户详细信息
export function getInfo() {
    return request({
        url: '/getInfo',
        method: 'get'
    })
}

// 退出方法
export function logout() {
    return request({
        url: '/logout',
        method: 'post'
    })
}

// 获取验证码
export function getCodeImg() {
    return request({
        url: '/captchaImage',
        headers: {
            isToken: false
        },
        method: 'get',
        timeout: 20000
    })
}
export function getModelsApi() {
    return request({
        url: '/models',
        method: 'get',
        timeout: 20000
    })
}

export function predictApi(data) {
    return request({
        url: '/predict',
        method: 'post',
        timeout: 20000,
        data: data
    })
}


//用户管理
export function getUsersApi(params) {
    return request({
        url: '/users',
        method: 'get',
        timeout: 20000,
        params: params
    })
}
export function createApi(data) {
    return request({
        url: '/users_creation',
        method: 'post',
        timeout: 20000,
        data: data
    })
}

export function updateApi(id,data) {
    return request({
        url: `/users/${id}`,
        method: 'put',
        timeout: 20000,
        data: data
    })
}
export function deleteApi(id) {
    return request({
        url: `/users/${id}`,
        method: 'delete',
        timeout: 20000,
    })
}
export function searchApi(id) {
    return request({
        url: `/users/${id}`,
        method: 'get',
        timeout: 20000,
    })
}


// 数据管理
export function getDatasApi(params) {
    return request({
        url: '/datasets',
        method: 'get',
        timeout: 20000,
        params: params
    })
}
export function createDatasetApi(data) {
    return request({
        url: '/dataset',
        method: 'post',
        timeout: 20000,
        data: data
    })
}

export function updateDatasetApi(id,data) {
    return request({
        url: `/dataset/${id}`,
        method: 'put',
        timeout: 20000,
        data: data
    })
}
export function deleteDatasetApi(id) {
    return request({
        url: `/dataset/${id}`,
        method: 'delete',
        timeout: 20000,
    })
}
export function searchDatasetApi(params) {
    return request({
        url: `/datasets/search`,
        method: 'get',
        timeout: 20000,
        params:params
    })
}
