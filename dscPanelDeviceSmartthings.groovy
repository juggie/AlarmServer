/**
 *  DSC Panel
 *
 *  Author: Kent Holloway <drizit@gmail.com>
 *  Date: 2014-03-20
 */
// for the UI
metadata {
	// Automatically generated. Make future change here.
	definition (name: "DSC Panel", author: "drizit@gmail.com") {
                // Change or define capabilities here as needed
		capability "Refresh"
		capability "Switch"
		capability "Contact Sensor"
		capability "Indicator"
		capability "Polling"

                // Add commands as needed
		command "open"
		command "closed"
                command "alarm"
		command "partitionready"
		command "partitionnotready"
   		command "partitionarmed"
   		command "partitionexitdelay"
   		command "partitionentrydelay"
   		command "partitionalarm"
	}

	simulator {
		// Nothing here, you could put some testing stuff here if you like
	}

    tiles {
        // NOTE: Leave the first item "panelstatus" alone
        // but edit all the remaining Tiles to match the zone numbers you care about
        // You have to change both the "zone1" name and the "device.zone1" type to match your zone
        // Then edit the details line further down in this section to match
        // all the zone numbers you setup or the icons will be missing in your app
        // You can add more rows if needed, just copy/paste the standardTile lines
        // for more
        
        // Final note: if you add/remove/change zones you have to force quit your
        // smartthings app on iOS (probably on Android also) to see the new tile layout
        
        // First Row
        standardTile("panelstatus", "device.panelstatus", width: 2, height: 2, canChangeBackground: true, canChangeIcon: true) {
            state "armed",     label: 'Armed',      backgroundColor: "#79b821", icon:"st.Home.home3"
            state "exitdelay", label: 'Exit Delay', backgroundColor: "#ff9900", icon:"st.Home.home3"
            state "entrydelay",label: 'EntryDelay', backgroundColor: "#ff9900", icon:"st.Home.home3"
            state "open",      label: 'Open',       backgroundColor: "#ffcc00", icon:"st.Home.home2"
            state "ready",     label: 'Ready',      backgroundColor: "#79b821", icon:"st.Home.home2"
            state "alarm",     label: 'Alarm',      backgroundColor: "#ff0000", icon:"st.Home.home3"
        }
        // Top right icon
		standardTile("zone1", "device.zone1", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.contact.contact.closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ff0000"
        }
        // 2nd row far right icon
		standardTile("zone2", "device.zone2", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.contact.contact.closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ff0000"
        }
        // third row from left to right
		standardTile("zone3", "device.zone3", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.contact.contact.closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ff0000"
        }
		standardTile("zone15", "device.zone15", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.doors.garage.garage-open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.doors.garage.garage-closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.doors.garage.garage-open",   backgroundColor: "#ff0000"
        }
 		standardTile("zone16", "device.zone16", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.doors.garage.garage-open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.doors.garage.garage-closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.doors.garage.garage-open",   backgroundColor: "#ff0000"
        }
 
       // Fourth row from left to right
 		standardTile("zone17", "device.zone17", canChangeBackground: true, canChangeIcon: true) {
			state "open",   label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ffa81e"
			state "closed", label: '${name}', icon: "st.contact.contact.closed", backgroundColor: "#79b821"
			state "alarm",  label: '${name}', icon: "st.contact.contact.open",   backgroundColor: "#ff0000"
        }

        // Fourth Row
        standardTile("refresh", "device.refresh", inactiveLabel: false, decoration: "flat") {
            state "default", action:"polling.poll", icon:"st.secondary.refresh"
        }

        // This tile will be the tile that is displayed on the Hub page.
        main "panelstatus"

        // These tiles will be displayed when clicked on the device, in the order listed here.
        details(["panelstatus", "zone1", "zone2", "zone3", "zone15", "zone16", "zone17", "refresh"])
    }
}

// parse events into attributes
def parse(String description) {
	// log.debug "Parsing '${description}'"
	// TODO: handle 'switch' attribute
	// TODO: handle 'indicatorStatus' attribute
	// TODO: handle '' attribute
    def myValues = description.tokenize()
    // log.debug "Description: ${myValues[0]} - ${myValues[1]}"
    sendEvent (name: "${myValues[0]}", value: "${myValues[1]}")
}

// handle commands
def open(String zone) {
    // log.debug "In Open function for Zone: $zone"
    sendEvent (name: "${zone}", value: 'open')
}

def closed(String zone) {
    // log.debug "In Closed function for Zone: $zone"
    sendEvent (name: "${zone}", value: 'closed')
}

def alarm(String zone) {
    // log.debug "Alarm for Zone: $zone"
    sendEvent (name: "${zone}", value: 'alarm')
}

def partitionready(String partition) {
    // log.debug "Partition ready: $partition"
    sendEvent (name: "panelstatus", value: 'ready')
}

def partitionnotready(String partition) {
    // log.debug "Partition not ready: $partition"
    sendEvent (name: "panelstatus", value: 'open')
}

def partitionarmed(String partition) {
    // log.debug "Partition Armed: $partition"
    sendEvent (name: "panelstatus", value: 'armed')
}

def partitionexitdelay(String partition) {
    // log.debug "Partition Exit Delay: $partition"
    sendEvent (name: "panelstatus", value: 'exitdelay')
}

def partitionentrydelay(String partition) {
    // log.debug "Partition Entry Delay: $partition"
    sendEvent (name: "panelstatus", value: 'entrydelay')
}

def partitionalarm(String partition) {
    // log.debug "Partition Alarm: $partition"
    sendEvent (name: "panelstatus", value: 'alarm')
}

def on() {
	log.debug "Executing 'on'"
	// TODO: handle 'on' command
}

def off() {
	log.debug "Executing 'off'"
	// TODO: handle 'off' command
}

def poll() {
	log.debug "Executing 'poll'"
	// TODO: handle 'poll' command
    // On poll what should we do? nothing for now..
}

def indicatorWhenOn() {
	log.debug "Executing 'indicatorWhenOn'"
	// TODO: handle 'indicatorWhenOn' command
}

def indicatorWhenOff() {
	log.debug "Executing 'indicatorWhenOff'"
	// TODO: handle 'indicatorWhenOff' command
}

def indicatorNever() {
	log.debug "Executing 'indicatorNever'"
	// TODO: handle 'indicatorNever' command
}

def refresh() {
	log.debug "Executing 'refresh' which is actually poll()"
    poll()
	// TODO: handle 'refresh' command
}

